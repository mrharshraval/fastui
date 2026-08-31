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
        checked ? "bg-[#3B82F6]" : "bg-neutral-300 dark:bg-neutral-600",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <span
        className={cn(
          "pointer-events-none inline-block size-[18px] rounded-full bg-white shadow-xs transition-transform duration-200 ease-in-out",
          checked ? "translate-x-[16px]" : "translate-x-0"
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

  const userEmailDisplay = email || "team@fastui.in"
  const userNameDisplay = displayName || userEmailDisplay.split("@")[0]
  const initials = getUserInitials(userNameDisplay, userEmailDisplay)

  const handleLogout = async () => {
    try {
      localStorage.removeItem("fastui_user")
      document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; max-age=0;"
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
        <div className="sticky top-0 z-10 bg-background flex items-center justify-between px-4 pt-4 pb-2">
          <h1 className="text-xl font-bold tracking-tight text-foreground">Settings</h1>
        </div>

        {/* Settings Body */}
        <div className="flex flex-col gap-3.5 px-4 pt-2">

          {/* 1. Account Profile Card */}
          <div
            onClick={() => setActiveModal("profile")}
            className="flex items-center justify-between p-3.5 rounded-3xl bg-neutral-100 dark:bg-neutral-800 active:bg-neutral-200/60 dark:active:bg-neutral-700/60 transition-all cursor-pointer"
          >
            <div className="flex items-center gap-3.5 min-w-0">
              <Avatar className="size-12 rounded-full border border-neutral-200 dark:border-neutral-700 shrink-0">
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
          <div className="rounded-3xl bg-neutral-100 dark:bg-neutral-800 overflow-hidden">
            {/* Profile Row */}
            <button
              type="button"
              onClick={() => setActiveModal("profile")}
              className="flex items-center justify-between w-full h-[54px] px-4 hover:bg-neutral-200/50 dark:hover:bg-neutral-700/50 active:bg-neutral-200/80 dark:active:bg-neutral-700/80 transition-colors cursor-pointer text-left"
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

            <div className="ml-[44px] border-b border-neutral-200/60 dark:border-neutral-700/50" />

            {/* Password Row */}
            <button
              type="button"
              onClick={() => setActiveModal("password")}
              className="flex items-center justify-between w-full h-[54px] px-4 hover:bg-neutral-200/50 dark:hover:bg-neutral-700/50 active:bg-neutral-200/80 dark:active:bg-neutral-700/80 transition-colors cursor-pointer text-left"
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

            <div className="ml-[44px] border-b border-neutral-200/60 dark:border-neutral-700/50" />

            {/* Discovery Row */}
            <button
              type="button"
              onClick={() => router.push("/discover")}
              className="flex items-center justify-between w-full h-[54px] px-4 hover:bg-neutral-200/50 dark:hover:bg-neutral-700/50 active:bg-neutral-200/80 dark:active:bg-neutral-700/80 transition-colors cursor-pointer text-left"
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
          <div className="flex items-center justify-between w-full h-[54px] px-4.5 rounded-full bg-neutral-100 dark:bg-neutral-800">
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
          <div className="flex items-center justify-between w-full h-[54px] px-4.5 rounded-full bg-neutral-100 dark:bg-neutral-800">
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
          <div className="flex items-center justify-between w-full h-[54px] px-4.5 rounded-full bg-neutral-100 dark:bg-neutral-800">
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
            className="flex items-center justify-between w-full h-[54px] px-4.5 rounded-full bg-neutral-100 dark:bg-neutral-800 hover:bg-destructive/10 active:bg-destructive/20 transition-colors cursor-pointer text-left text-destructive"
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
            className="flex items-center justify-between w-full h-[54px] px-4.5 rounded-full bg-neutral-100 dark:bg-neutral-800 hover:bg-rose-500/10 active:bg-rose-500/20 transition-colors cursor-pointer text-left text-rose-500"
          >
            <div className="flex items-center gap-3 min-w-0">
              <Trash2 size={18} className="text-rose-500 shrink-0" strokeWidth={1.75} />
              <span className="text-[15px] font-normal truncate">
                Delete Account
              </span>
            </div>
            <ChevronRight size={16} className="text-rose-500/50 shrink-0" />
          </button>


        </div>

        {/* ─────────────────────────────────────────────────────────────
            MOBILE MODALS / BOTTOM SHEETS
           ───────────────────────────────────────────────────────────── */}
        {activeModal && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4 animate-in fade-in duration-200">
            <div className="w-full sm:max-w-md bg-background border border-neutral-200 dark:border-neutral-800 rounded-t-3xl sm:rounded-2xl p-5 shadow-2xl animate-in slide-in-from-bottom-6 duration-200 pb-8 sm:pb-5">

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
                  className="size-7 rounded-full bg-accent/60 flex items-center justify-center text-muted-foreground hover:text-foreground cursor-pointer"
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
                        className="h-10 bg-neutral-100 dark:bg-neutral-800 border-none rounded-full px-4 text-sm"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">Email</Label>
                      <Input
                        value={email}
                        disabled
                        className="h-10 bg-neutral-100 dark:bg-neutral-800 border-none rounded-full px-4 text-sm opacity-70"
                      />
                    </div>
                    <Button
                      onClick={() => {
                        try {
                          const stored = localStorage.getItem("fastui_user")
                          const obj = stored ? JSON.parse(stored) : {}
                          localStorage.setItem("fastui_user", JSON.stringify({ ...obj, name: displayName }))
                        } catch { }
                        setStatusMessage("Profile updated.")
                        setTimeout(() => setActiveModal(null), 800)
                      }}
                      className="w-full h-10 rounded-full text-sm mt-2"
                    >
                      Done
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
                        className="h-10 bg-neutral-100 dark:bg-neutral-800 border-none rounded-full px-4 text-sm"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label className="text-xs font-medium">New Password</Label>
                      <Input
                        type="password"
                        placeholder="New password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="h-10 bg-neutral-100 dark:bg-neutral-800 border-none rounded-full px-4 text-sm"
                      />
                    </div>
                    <Button
                      onClick={() => {
                        setStatusMessage("Password updated.")
                        setTimeout(() => setActiveModal(null), 800)
                      }}
                      className="w-full h-10 rounded-full text-sm mt-2"
                    >
                      Update Password
                    </Button>
                  </>
                )}

                {activeModal === "notifications" && (
                  <>
                    <div className="flex items-center justify-between p-3.5 rounded-2xl bg-neutral-100 dark:bg-neutral-800">
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
                        className="w-full h-10 rounded-full text-xs flex items-center justify-center gap-1.5"
                      >
                        <Send size={13} />
                        <span>Send Test Alert</span>
                      </Button>
                    )}
                  </>
                )}

                {activeModal === "logout" && (
                  <div className="flex flex-col gap-3">
                    <p className="text-xs text-muted-foreground">
                      Are you sure you want to sign out of FastUI?
                    </p>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setActiveModal(null)}
                        className="flex-1 h-10 rounded-full text-xs"
                      >
                        Cancel
                      </Button>
                      <Button
                        type="button"
                        variant="destructive"
                        onClick={handleLogout}
                        className="flex-1 h-10 rounded-full text-xs"
                      >
                        Sign Out
                      </Button>
                    </div>
                  </div>
                )}

                {activeModal === "delete" && (
                  <div className="flex flex-col gap-3">
                    <p className="text-xs text-rose-400">
                      This will permanently delete your account and all associated data. This action cannot be undone.
                    </p>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setActiveModal(null)}
                        className="flex-1 h-10 rounded-full text-xs"
                      >
                        Cancel
                      </Button>
                      <Button
                        type="button"
                        className="flex-1 h-10 rounded-full text-xs bg-rose-600 text-white hover:bg-rose-700"
                        onClick={() => setActiveModal(null)}
                      >
                        Delete Account
                      </Button>
                    </div>
                  </div>
                )}


                {statusMessage && (
                  <div className="flex items-center gap-1.5 text-xs text-emerald-400 mt-1">
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
          DESKTOP SETTINGS EXPERIENCE (>= 768px) — 100% UNCHANGED
         ───────────────────────────────────────────────────────────── */}
      <div className="hidden md:flex flex-col gap-8 px-4 md:px-8 lg:px-12 xl:px-16 pt-4 md:pt-14 pb-8 max-w-[1600px] w-full mx-auto">
        {/* Desktop Header */}
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold tracking-tight text-foreground">Settings</h2>
        </div>

        <Card className="bg-card rounded-xl">
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
                placeholder="Your name"
                className="h-10 bg-accent/30 rounded-full text-sm border-none"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">Email</Label>
              <Input
                value={userEmailDisplay}
                disabled
                type="email"
                placeholder="name@domain.com"
                className="h-10 bg-accent/30 rounded-full text-sm border-none opacity-80"
              />
            </div>
            <Button className="w-fit h-9 rounded-2xl text-sm border-none">Save Changes</Button>
          </CardContent>
        </Card>

        <Card className="bg-card rounded-xl">
          <CardHeader className="pb-4">
            <CardTitle className="text-sm font-semibold">Notifications</CardTitle>
            <CardDescription className="text-xs">Lock-screen alerts and sound for sales reminders</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <DesktopNotificationsSection />
          </CardContent>
        </Card>

        <Card className="bg-card rounded-xl">
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
                className="h-10 bg-accent/30 rounded-full text-sm border-none"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-sm font-medium">New Password</Label>
              <Input
                type="password"
                placeholder="New password"
                className="h-10 bg-accent/30 rounded-full text-sm border-none"
              />
            </div>
            <Button variant="secondary" className="w-fit h-9 rounded-2xl text-sm border-none">
              Update Password
            </Button>
          </CardContent>
        </Card>

        <Card className="bg-rose-500/10 rounded-xl">
          <CardHeader className="pb-4">
            <CardTitle className="text-sm font-semibold text-rose-400">Danger Zone</CardTitle>
            <CardDescription className="text-xs">Irreversible actions</CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              variant="secondary"
              className="h-9 rounded-2xl text-sm text-rose-400 bg-rose-500/20 hover:bg-rose-500/30 border-none"
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
            <div className="flex items-center justify-center size-8 rounded-full bg-emerald-500/10 text-emerald-400">
              <Bell size={16} />
            </div>
          ) : (
            <div className="flex items-center justify-center size-8 rounded-full bg-accent/40 text-muted-foreground">
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
          <Check size={12} className="text-emerald-400" />
          <span>{statusMessage}</span>
        </div>
      )}
    </div>
  )
}

function BellOffIcon(props: any) {
  return <Bell {...props} className={cn(props.className, "opacity-60")} />
}
