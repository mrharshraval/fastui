"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { useTheme } from "@/components/theme-provider"
import { api } from "@/lib/api"
import { cn } from "@/lib/utils"
import {
  isPushNotificationSupported,
  getNotificationPermissionState,
  getExistingPushSubscription,
  subscribeToPushNotifications,
  unsubscribeFromPushNotifications,
  sendTestPushNotification,
} from "@/lib/push-notifications"
import {
  ChevronRight,
  User,
  Lock,
  Sun,
  Moon,
  Bell,
  LogOut,
  Trash2,
  Check,
  Send,
  Sparkles,
  Info,
  X,
} from "lucide-react"

interface AuthUser {
  user_id?: number
  email?: string
  name?: string
  role?: string
}

function getUserInitials(name?: string | null, email?: string | null) {
  if (name) {
    const parts = name.trim().split(" ")
    if (parts.length > 1) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
    return parts[0].substring(0, 2).toUpperCase()
  }
  if (email) return email.substring(0, 2).toUpperCase()
  return "FA"
}

function MinimalSwitch({
  checked,
  onChange,
  disabled,
}: {
  checked: boolean
  onChange: (val: boolean) => void
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative inline-flex h-[22px] w-[38px] shrink-0 cursor-pointer rounded-full p-[2px] transition-colors duration-200 ease-in-out focus:outline-none active:scale-95",
        checked ? "bg-primary" : "bg-input border border-border/50",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <span
        className={cn(
          "pointer-events-none inline-block size-[18px] rounded-full transition-transform duration-200 ease-in-out",
          checked ? "translate-x-[16px] bg-primary-foreground" : "translate-x-0 bg-foreground/80"
        )}
      />
    </button>
  )
}

export default function SettingsPage() {
  const router = useRouter()
  const { resolvedTheme, setTheme } = useTheme()

  // User state
  const [currentUser, setCurrentUser] = React.useState<AuthUser | null>(null)
  const [displayName, setDisplayName] = React.useState("")
  const [email, setEmail] = React.useState("")
  const [currentPassword, setCurrentPassword] = React.useState("")
  const [newPassword, setNewPassword] = React.useState("")
  const [savingProfile, setSavingProfile] = React.useState(false)
  const [updatingPassword, setUpdatingPassword] = React.useState(false)

  // Mobile sub-sheets / modals
  const [activeModal, setActiveModal] = React.useState<"profile" | "password" | "notifications" | "logout" | "delete" | null>(null)
  const [statusMessage, setStatusMessage] = React.useState<string | null>(null)

  // Push notification state
  const [pushSupported, setPushSupported] = React.useState<boolean>(true)
  const [pushSubscribed, setPushSubscribed] = React.useState<boolean>(false)
  const [pushLoading, setPushLoading] = React.useState<boolean>(false)

  React.useEffect(() => {
    // 1. Initial local storage load
    try {
      const stored = localStorage.getItem("fastui_user")
      if (stored) {
        const parsed = JSON.parse(stored)
        if (parsed?.email) {
          setCurrentUser(parsed)
          setEmail(parsed.email || "")
          setDisplayName(parsed.name || parsed.email.split("@")[0])
        }
      }
    } catch { }

    // 2. Fetch authoritative user from API
    api.get<AuthUser>("/auth/me")
      .then((data) => {
        if (data && data.email) {
          setCurrentUser(data)
          setEmail(data.email || "")
          const nameVal = data.name || data.email.split("@")[0]
          setDisplayName(nameVal.charAt(0).toUpperCase() + nameVal.slice(1))
          try {
            localStorage.setItem("fastui_user", JSON.stringify(data))
          } catch { }
        }
      })
      .catch(() => { })

    // 3. Check push notifications
    const isSupp = isPushNotificationSupported()
    setPushSupported(isSupp)
    if (isSupp) {
      getExistingPushSubscription().then((sub) => {
        const perm = getNotificationPermissionState()
        setPushSubscribed(!!sub && perm === "granted")
      })
    }
  }, [])

  const userEmailDisplay = email
  const userNameDisplay = displayName || (userEmailDisplay ? userEmailDisplay.split("@")[0] : "Account")
  const initials = getUserInitials(userNameDisplay || null, userEmailDisplay || null)

  const handleSaveProfile = async () => {
    if (!displayName.trim() || savingProfile) return
    try {
      setSavingProfile(true)
      const res = await api.patch<AuthUser>("/auth/me", { name: displayName.trim() })
      if (res) {
        setCurrentUser(res)
        try {
          localStorage.setItem("fastui_user", JSON.stringify(res))
        } catch { }
      }
      setStatusMessage("Profile updated.")
      setTimeout(() => {
        setStatusMessage(null)
        setActiveModal(null)
      }, 1000)
    } catch (err: any) {
      setStatusMessage(err?.message || "Failed to update profile.")
    } finally {
      setSavingProfile(false)
    }
  }

  const handlePasswordUpdate = async () => {
    if (!currentPassword || !newPassword || updatingPassword) return
    try {
      setUpdatingPassword(true)
      await api.put("/auth/password", {
        current_password: currentPassword,
        new_password: newPassword
      })
      setCurrentPassword("")
      setNewPassword("")
      setStatusMessage("Password updated.")
      setTimeout(() => {
        setStatusMessage(null)
        setActiveModal(null)
      }, 1200)
    } catch (err: any) {
      setStatusMessage(err?.message || "Incorrect current password.")
    } finally {
      setUpdatingPassword(false)
    }
  }

  const handleLogout = async () => {
    try {
      localStorage.removeItem("fastui_user")
      await api.post("/auth/logout", {})
    } catch { }
    window.location.href = "/login"
  }

  const handleTogglePush = async (nextVal?: boolean) => {
    setPushLoading(true)
    setStatusMessage(null)

    const shouldEnable = nextVal !== undefined ? nextVal : !pushSubscribed

    if (!shouldEnable) {
      const res = await unsubscribeFromPushNotifications()
      if (res.success) {
        setPushSubscribed(false)
        setStatusMessage("Notifications turned off.")
      } else {
        setStatusMessage(res.error || "Failed to turn off notifications.")
      }
    } else {
      const res = await subscribeToPushNotifications()
      if (res.success) {
        setPushSubscribed(true)
        setStatusMessage("Phone notifications active.")
      } else {
        setStatusMessage(res.error || "Failed to enable notifications.")
      }
    }
    setPushLoading(false)
  }

  const handleSendTestPush = async () => {
    setPushLoading(true)
    setStatusMessage(null)
    try {
      await sendTestPushNotification(
        "FastUI Reminder",
        "Phone notifications are active! You will receive reminder alerts."
      )
      setStatusMessage("Test alert sent.")
    } catch {
      setStatusMessage("Could not deliver test notification.")
    } finally {
      setPushLoading(false)
    }
  }

  return (
    <>
      {/* ─────────────────────────────────────────────────────────────
          MOBILE MINIMAL GROUPED SETTINGS EXPERIENCE (< 768px)
         ───────────────────────────────────────────────────────────── */}
      <div className="md:hidden flex flex-col min-h-screen bg-background pb-32">
        {/* Mobile Header */}
        <div className="sticky top-0 z-10 bg-background/80 backdrop-blur-md flex items-center justify-between px-4 pt-4 pb-2 border-b border-border/40">
          <h1 className="text-xl font-bold tracking-tight text-foreground">Settings</h1>
        </div>

        {/* Settings Body */}
        <div className="flex flex-col gap-3.5 px-4 pt-3">

          {/* 1. Account Profile Card */}
          <div
            onClick={() => setActiveModal("profile")}
            className="flex items-center justify-between p-3.5 rounded-3xl bg-card border-none active:bg-muted/70 transition-all cursor-pointer shadow-none"
          >
            <div className="flex items-center gap-3.5 min-w-0">
              <Avatar className="size-12 rounded-full border border-border/50 shrink-0">
                <AvatarFallback className="text-sm font-bold bg-foreground text-background">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div className="flex flex-col min-w-0">
                <span className="text-[16px] font-medium text-foreground leading-snug truncate">
                  {userNameDisplay}
                </span>
                <span className="text-[13px] text-muted-foreground leading-tight truncate mt-0.5">
                  {userEmailDisplay}
                </span>
              </div>
            </div>
            <ChevronRight className="size-4 text-muted-foreground/60 shrink-0 ml-2" />
          </div>

          {/* 2. Account Group (Multi-row rounded-3xl) */}
          <div className="rounded-3xl bg-card border-none overflow-hidden shadow-none">
            {/* Profile Row */}
            <button
              type="button"
              onClick={() => setActiveModal("profile")}
              className="flex items-center justify-between w-full h-[54px] px-4 hover:bg-muted/50 active:bg-muted/80 transition-colors cursor-pointer text-left"
            >
              <div className="flex items-center gap-3 min-w-0">
                <User size={18} className="text-foreground shrink-0" strokeWidth={1.75} />
                <span className="text-[15px] font-normal text-foreground truncate">
                  Profile
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-muted-foreground shrink-0">
                <span className="text-[14px] truncate max-w-[120px]">{userNameDisplay}</span>
                <ChevronRight size={16} className="text-muted-foreground/60" />
              </div>
            </button>

            <div className="ml-[44px] border-b border-border/40" />

            {/* Password Row */}
            <button
              type="button"
              onClick={() => setActiveModal("password")}
              className="flex items-center justify-between w-full h-[54px] px-4 hover:bg-muted/50 active:bg-muted/80 transition-colors cursor-pointer text-left"
            >
              <div className="flex items-center gap-3 min-w-0">
                <Lock size={18} className="text-foreground shrink-0" strokeWidth={1.75} />
                <span className="text-[15px] font-normal text-foreground truncate">
                  Password
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-muted-foreground shrink-0">
                <span className="text-[14px]">••••••••</span>
                <ChevronRight size={16} className="text-muted-foreground/60" />
              </div>
            </button>

            <div className="ml-[44px] border-b border-border/40" />

            {/* Discovery Row */}
            <button
              type="button"
              onClick={() => router.push("/discover")}
              className="flex items-center justify-between w-full h-[54px] px-4 hover:bg-muted/50 active:bg-muted/80 transition-colors cursor-pointer text-left"
            >
              <div className="flex items-center gap-3 min-w-0">
                <Sparkles size={18} className="text-foreground shrink-0" strokeWidth={1.75} />
                <span className="text-[15px] font-normal text-foreground truncate">
                  Discovery Engine
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-muted-foreground shrink-0">
                <span className="text-[14px]">Auto</span>
                <ChevronRight size={16} className="text-muted-foreground/60" />
              </div>
            </button>
          </div>

          {/* 3. Push Notifications Row (Single-row rounded-full) */}
          <div className="flex items-center justify-between w-full h-[54px] px-4.5 rounded-full bg-card border-none shadow-none">
            <div className="flex items-center gap-3 min-w-0">
              <Bell size={18} className="text-foreground shrink-0" strokeWidth={1.75} />
              <span className="text-[15px] font-normal text-foreground truncate">
                Push Notifications
              </span>
            </div>
            <MinimalSwitch
              checked={pushSubscribed}
              onChange={handleTogglePush}
              disabled={pushLoading}
            />
          </div>

          {/* 4. Dark Mode Row (Single-row rounded-full) */}
          <div className="flex items-center justify-between w-full h-[54px] px-4.5 rounded-full bg-card border-none shadow-none">
            <div className="flex items-center gap-3 min-w-0">
              {resolvedTheme === "dark" ? (
                <Moon size={18} className="text-foreground shrink-0" strokeWidth={1.75} />
              ) : (
                <Sun size={18} className="text-foreground shrink-0" strokeWidth={1.75} />
              )}
              <span className="text-[15px] font-normal text-foreground truncate">
                Dark Mode
              </span>
            </div>
            <MinimalSwitch
              checked={resolvedTheme === "dark"}
              onChange={(checked) => setTheme(checked ? "dark" : "light")}
            />
          </div>

          {/* 5. General / About Row (Single-row rounded-full) */}
          <div className="flex items-center justify-between w-full h-[54px] px-4.5 rounded-full bg-card border-none shadow-none">
            <div className="flex items-center gap-3 min-w-0">
              <Info size={18} className="text-foreground shrink-0" strokeWidth={1.75} />
              <span className="text-[15px] font-normal text-foreground truncate">
                Version
              </span>
            </div>
            <span className="text-[14px] text-muted-foreground font-mono">1.0.0</span>
          </div>

          {/* 6. Account Action: Sign Out (Single-row rounded-full) */}
          <button
            type="button"
            onClick={() => setActiveModal("logout")}
            className="flex items-center justify-between w-full h-[54px] px-4.5 rounded-full bg-card border-none hover:bg-destructive-muted/30 active:bg-destructive-muted/60 transition-colors cursor-pointer text-left text-destructive shadow-none"
          >
            <div className="flex items-center gap-3 min-w-0">
              <LogOut size={18} className="text-destructive shrink-0" strokeWidth={1.75} />
              <span className="text-[15px] font-normal truncate">
                Sign Out
              </span>
            </div>
            <ChevronRight size={16} className="text-destructive/50 shrink-0" />
          </button>

          {/* 7. Danger Zone: Delete Account (Single-row rounded-full) */}
          <button
            type="button"
            onClick={() => setActiveModal("delete")}
            className="flex items-center justify-between w-full h-[54px] px-4.5 rounded-full bg-card border-none hover:bg-destructive-muted/30 active:bg-destructive-muted/60 transition-colors cursor-pointer text-left text-destructive shadow-none"
          >
            <div className="flex items-center gap-3 min-w-0">
              <Trash2 size={18} className="text-destructive shrink-0" strokeWidth={1.75} />
              <span className="text-[15px] font-normal truncate">
                Delete Account
              </span>
            </div>
            <ChevronRight size={16} className="text-destructive/50 shrink-0" />
          </button>

        </div>

        {/* ─────────────────────────────────────────────────────────────
            MOBILE MODALS / BOTTOM SHEETS
           ───────────────────────────────────────────────────────────── */}
        {activeModal && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4 animate-in fade-in duration-200">
            <div className="w-full sm:max-w-md bg-background border-none rounded-t-3xl sm:rounded-2xl p-5 shadow-none animate-in slide-in-from-bottom-6 duration-200 pb-8 sm:pb-5">

              {/* Header with Close */}
              <div className="flex items-center justify-between pb-3 border-b border-border/30">
                <h3 className="text-sm font-semibold text-foreground">
                  {activeModal === "profile" && "Profile Details"}
                  {activeModal === "password" && "Change Password"}
                  {activeModal === "notifications" && "Push Notifications"}
                  {activeModal === "logout" && "Sign Out"}
                  {activeModal === "delete" && "Delete Account"}
                </h3>
                <button
                  type="button"
                  onClick={() => { setActiveModal(null); setStatusMessage(null) }}
                  className="size-7 rounded-full bg-secondary flex items-center justify-center text-muted-foreground hover:text-foreground cursor-pointer"
                >
                  <X size={14} />
                </button>
              </div>

              {/* Modal Body */}
              <div className="pt-4 flex flex-col gap-4">
                {activeModal === "profile" && (
                  <>
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Display Name</Label>
                      <Input
                        value={displayName}
                        onChange={(e) => setDisplayName(e.target.value)}
                        className="h-10 bg-input border border-border/50 rounded-full px-4 text-sm"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Email</Label>
                      <Input
                        value={email}
                        disabled
                        className="h-10 bg-input border border-border/50 rounded-full px-4 text-sm opacity-70"
                      />
                    </div>
                    <Button
                      onClick={handleSaveProfile}
                      disabled={savingProfile}
                      className="w-full h-10 rounded-full text-sm mt-2"
                    >
                      {savingProfile ? "Saving..." : "Done"}
                    </Button>
                  </>
                )}

                {activeModal === "password" && (
                  <>
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Current Password</Label>
                      <Input
                        type="password"
                        placeholder="Current password"
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        className="h-10 bg-input border border-border/50 rounded-full px-4 text-sm"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">New Password</Label>
                      <Input
                        type="password"
                        placeholder="New password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="h-10 bg-input border border-border/50 rounded-full px-4 text-sm"
                      />
                    </div>
                    <Button
                      onClick={handlePasswordUpdate}
                      disabled={updatingPassword}
                      className="w-full h-10 rounded-full text-sm mt-2"
                    >
                      {updatingPassword ? "Updating..." : "Update Password"}
                    </Button>
                  </>
                )}

                {activeModal === "notifications" && (
                  <>
                    <div className="flex items-center justify-between p-3.5 rounded-2xl bg-card border-none shadow-none">
                      <div>
                        <p className="text-xs font-medium text-foreground">
                          {pushSubscribed ? "Active on this device" : "Turned off"}
                        </p>
                        <p className="text-[11px] text-muted-foreground mt-0.5">
                          {pushSubscribed ? "Lock-screen alerts for due reminders." : "Enable to get reminder notifications."}
                        </p>
                      </div>
                      <MinimalSwitch
                        checked={pushSubscribed}
                        onChange={handleTogglePush}
                        disabled={pushLoading}
                      />
                    </div>

                    {pushSubscribed && (
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={handleSendTestPush}
                        disabled={pushLoading}
                        className="w-full h-10 rounded-full text-xs font-medium flex items-center justify-center gap-1.5 cursor-pointer mt-2"
                      >
                        <Send size={13} />
                        Send Test Notification
                      </Button>
                    )}
                  </>
                )}

                {activeModal === "logout" && (
                  <div className="flex flex-col gap-3 pt-1">
                    <p className="text-xs text-muted-foreground">
                      Are you sure you want to sign out of FastUI?
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="secondary"
                        onClick={() => setActiveModal(null)}
                        className="flex-1 h-10 rounded-full text-xs font-medium"
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleLogout}
                        className="flex-1 h-10 rounded-full text-xs font-medium"
                      >
                        Sign Out
                      </Button>
                    </div>
                  </div>
                )}

                {activeModal === "delete" && (
                  <div className="flex flex-col gap-3 pt-1">
                    <p className="text-xs text-muted-foreground">
                      This action cannot be undone. All your business records, tasks, and data will be permanently removed.
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="secondary"
                        onClick={() => setActiveModal(null)}
                        className="flex-1 h-10 rounded-full text-xs font-medium"
                      >
                        Cancel
                      </Button>
                      <Button
                        variant="destructive"
                        onClick={handleLogout}
                        className="flex-1 h-10 rounded-full text-xs font-medium"
                      >
                        Delete Account
                      </Button>
                    </div>
                  </div>
                )}

                {statusMessage && (
                  <div className="flex items-center gap-1.5 text-xs text-success mt-1">
                    <Check size={13} />
                    <span>{statusMessage}</span>
                  </div>
                )}
              </div>

            </div>
          </div>
        )}
      </div>

      {/* ─────────────────────────────────────────────────────────────
          DESKTOP VIEW (Settings Cards Grid)
          Visible on screen >= md
         ───────────────────────────────────────────────────────────── */}
      <div className="hidden md:flex flex-col gap-6 px-8 lg:px-12 xl:px-16 pt-14 pb-12 max-w-4xl mx-auto w-full">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground">Settings</h2>
          <p className="text-xs text-muted-foreground mt-0.5">Manage your preferences and workspace configuration</p>
        </div>

        {statusMessage && (
          <div className="flex items-center gap-2 p-3 rounded-2xl bg-primary/10 border border-primary/20 text-foreground text-xs font-medium animate-in fade-in">
            <Info size={14} className="text-primary shrink-0" />
            <span>{statusMessage}</span>
          </div>
        )}

        <Card className="bg-card rounded-xl border-none shadow-none">
          <CardHeader className="pb-4">
            <CardTitle className="text-sm font-semibold">Profile</CardTitle>
            <CardDescription className="text-xs">Update your name and email</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">Display Name</Label>
              <Input
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Your Name"
                className="h-10 bg-input border border-border/50 rounded-full text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">Email</Label>
              <Input
                value={userEmailDisplay}
                disabled
                type="email"
                placeholder="name@domain.com"
                className="h-10 bg-input border border-border/50 rounded-full text-sm opacity-80"
              />
            </div>
            <Button
              onClick={handleSaveProfile}
              disabled={savingProfile}
              className="w-fit h-9 rounded-2xl text-sm"
            >
              {savingProfile ? "Saving..." : "Save Changes"}
            </Button>
          </CardContent>
        </Card>

        <Card className="bg-card rounded-xl border-none shadow-none">
          <CardHeader className="pb-4">
            <CardTitle className="text-sm font-semibold">Notifications</CardTitle>
            <CardDescription className="text-xs">Lock-screen alerts and sound for sales reminders</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <DesktopNotificationsSection />
          </CardContent>
        </Card>

        <Card className="bg-card rounded-xl border-none shadow-none">
          <CardHeader className="pb-4">
            <CardTitle className="text-sm font-semibold">Password</CardTitle>
            <CardDescription className="text-xs">Update your password</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">Current Password</Label>
              <Input
                type="password"
                placeholder="Current password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="h-10 bg-input border border-border/50 rounded-full text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">New Password</Label>
              <Input
                type="password"
                placeholder="New password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="h-10 bg-input border border-border/50 rounded-full text-sm"
              />
            </div>
            <Button
              variant="secondary"
              onClick={handlePasswordUpdate}
              disabled={updatingPassword}
              className="w-fit h-9 rounded-2xl text-sm"
            >
              {updatingPassword ? "Updating..." : "Update Password"}
            </Button>
          </CardContent>
        </Card>

        <Card className="bg-destructive-muted/30 border-none rounded-xl shadow-none">
          <CardHeader className="pb-4">
            <CardTitle className="text-sm font-semibold text-destructive">Danger Zone</CardTitle>
            <CardDescription className="text-xs">Irreversible actions</CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              variant="destructive"
              className="h-9 rounded-2xl text-sm"
            >
              Delete Account
            </Button>
          </CardContent>
        </Card>
      </div>
    </>
  )
}

function DesktopNotificationsSection() {
  const [supported, setSupported] = React.useState<boolean>(true)
  const [isSubscribed, setIsSubscribed] = React.useState<boolean>(false)
  const [loading, setLoading] = React.useState<boolean>(true)
  const [actionLoading, setActionLoading] = React.useState<boolean>(false)
  const [statusMessage, setStatusMessage] = React.useState<string | null>(null)

  React.useEffect(() => {
    async function checkStatus() {
      const isSupp = isPushNotificationSupported()
      setSupported(isSupp)
      if (isSupp) {
        const sub = await getExistingPushSubscription()
        const perm = getNotificationPermissionState()
        setIsSubscribed(!!sub && perm === "granted")
      }
      setLoading(false)
    }
    checkStatus()
  }, [])

  const handleToggle = async () => {
    setActionLoading(true)
    setStatusMessage(null)

    if (isSubscribed) {
      const res = await unsubscribeFromPushNotifications()
      if (res.success) {
        setIsSubscribed(false)
        setStatusMessage("Notifications turned off.")
      } else {
        setStatusMessage(res.error || "Failed to turn off notifications.")
      }
    } else {
      const res = await subscribeToPushNotifications()
      if (res.success) {
        setIsSubscribed(true)
        setStatusMessage("Phone notifications enabled.")
      } else {
        setStatusMessage(res.error || "Failed to enable notifications.")
      }
    }
    setActionLoading(false)
  }

  const handleTest = async () => {
    setActionLoading(true)
    setStatusMessage(null)
    try {
      await sendTestPushNotification(
        "FastUI Reminder",
        "Phone notifications are active! You will receive reminder alerts."
      )
      setStatusMessage("Test notification sent.")
    } catch {
      setStatusMessage("Could not deliver test notification.")
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return <div className="text-xs text-muted-foreground">Checking notification status…</div>
  }

  if (!supported) {
    return (
      <div className="text-xs text-muted-foreground">
        Push notifications are not supported on this browser. On iPhone, add FastUI to your Home Screen to enable lock-screen alerts.
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isSubscribed ? (
            <div className="flex items-center justify-center size-8 rounded-full bg-success-muted text-success">
              <Bell size={16} />
            </div>
          ) : (
            <div className="flex items-center justify-center size-8 rounded-full bg-secondary text-muted-foreground">
              <BellOffIcon size={16} />
            </div>
          )}
          <div>
            <p className="text-xs font-medium text-foreground">
              {isSubscribed ? "Active on this device" : "Turned off on this device"}
            </p>
            <p className="text-[11px] text-muted-foreground">
              {isSubscribed ? "Reminders will trigger lock-screen alerts and sounds." : "Enable to get reminder alerts on your phone."}
            </p>
          </div>
        </div>

        <Button
          type="button"
          onClick={handleToggle}
          disabled={actionLoading}
          variant={isSubscribed ? "outline" : "default"}
          className="h-8 px-3 rounded-full text-xs shrink-0"
        >
          {actionLoading ? "Updating…" : isSubscribed ? "Disable" : "Enable"}
        </Button>
      </div>

      {isSubscribed && (
        <div className="flex items-center justify-between pt-2 border-t border-border/30">
          <span className="text-xs text-muted-foreground">Send a test notification</span>
          <Button
            type="button"
            variant="secondary"
            onClick={handleTest}
            disabled={actionLoading}
            className="h-7 px-2.5 rounded-full text-[11px] flex items-center gap-1.5 shrink-0"
          >
            <Send size={12} />
            <span>Send Test Alert</span>
          </Button>
        </div>
      )}

      {statusMessage && (
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-1">
          <Check size={12} className="text-success" />
          <span>{statusMessage}</span>
        </div>
      )}
    </div>
  )
}

function BellOffIcon(props: any) {
  return <Bell {...props} className={cn(props.className, "opacity-60")} />
}
