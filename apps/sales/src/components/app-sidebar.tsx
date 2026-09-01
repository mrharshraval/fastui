"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { api } from "@/lib/api"
import {
  LayoutDashboard,
  Compass,
  UserSearch,
  Users,
  Building2,
  Contact,
  Activity,
  GitBranch,
  Bell,
  BarChart3,
  Settings,
  LogOut,
  UserCircle,
  ChevronsUpDown,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useTheme } from "@/components/theme-provider"
import { Moon, Sun } from "lucide-react"
import { DESKTOP_NAV_ITEMS } from "@/config/navigation"

function getUserInitials(name?: string | null, email?: string | null) {
  if (name) {
    const parts = name.split(" ")
    if (parts.length > 1) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
    return parts[0].substring(0, 2).toUpperCase()
  }
  if (email) return email.substring(0, 2).toUpperCase()
  return "FA"
}

interface AuthUser {
  user_id?: number
  email?: string
  role?: string
}

export function AppSidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { state, setOpen, setOpenMobile, isMobile } = useSidebar()
  const { resolvedTheme, setTheme } = useTheme()
  const [currentUser, setCurrentUser] = React.useState<AuthUser | null>(null)

  React.useEffect(() => {
    // 1. Instant hydration from client storage if available
    try {
      const stored = localStorage.getItem("fastui_user")
      if (stored) {
        const parsed = JSON.parse(stored)
        if (parsed?.email) {
          setCurrentUser(parsed)
        }
      }
    } catch {}

    // 2. Authoritative sync from backend session
    api.get<AuthUser>("/auth/me")
      .then((data) => {
        if (data && data.email) {
          setCurrentUser(data)
          try {
            localStorage.setItem("fastui_user", JSON.stringify(data))
          } catch {}
        }
      })
      .catch(() => {})
  }, [])

  const userEmail = currentUser?.email ?? ""
  const rawUsername = userEmail ? userEmail.split("@")[0] : "Account"
  const displayName = rawUsername.charAt(0).toUpperCase() + rawUsername.slice(1)
  const initials = getUserInitials(displayName || null, userEmail || null)

  const side = isMobile ? "top" : (state === "collapsed" ? "right" : "top")
  const align = isMobile ? "center" : (state === "collapsed" ? "end" : "start")

  const handleSidebarClick = (e: React.MouseEvent) => {
    if (state === "collapsed") {
      const target = e.target as HTMLElement
      const isMenuItem = target.closest('[data-sidebar="menu-button"]')
      if (!isMenuItem) setOpen(true)
    }
  }

  const handleLogout = async () => {
    try {
      localStorage.removeItem("fastui_user")
      // Note: HttpOnly cookies cannot be cleared from JavaScript.
      // The authoritative cookie deletion happens server-side via /auth/logout.
      await api.post("/auth/logout", {})
    } catch {}
    window.location.href = "/login"
  }

  return (
    <Sidebar collapsible="icon" onClick={handleSidebarClick}>

      {/* Header */}
      <SidebarHeader className="flex-row items-center px-1.5 h-12 shrink-0 relative">
        {/* Collapsed Mode: Clean mark toggle */}
        <div className="hidden group-data-[collapsible=icon]:flex items-center justify-center w-full">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              setOpen(true)
            }}
            className="group/logo-toggle relative flex items-center justify-center size-10 rounded-xl text-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors cursor-pointer"
            title="Expand sidebar"
          >
            {/* 1. Default State: Brand Mark */}
            <div className="flex items-center justify-center size-9 transition-opacity duration-150 group-hover/logo-toggle:opacity-0">
              <img
                src="/assets/brand/mark/monochrome/black.svg"
                alt="fastui"
                className="size-6 shrink-0 dark:hidden"
              />
              <img
                src="/assets/brand/mark/monochrome/white.svg"
                alt="fastui"
                className="size-6 shrink-0 hidden dark:block"
              />
            </div>

            {/* 2. Hover State: Sidebar Toggle Expand Icon */}
            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover/logo-toggle:opacity-100 transition-opacity duration-150">
              <PanelLeftOpen className="size-5" />
            </div>
          </button>
        </div>

        {/* Expanded Mode: Mark + Wordmark + Right-Aligned Collapse Toggle */}
        <div className="flex items-center justify-between w-full group-data-[collapsible=icon]:hidden">
          <div className="flex items-center gap-2 pl-1.5">
            <img
              src="/assets/brand/mark/monochrome/black.svg"
              alt="fastui"
              className="size-6 shrink-0 dark:hidden"
            />
            <img
              src="/assets/brand/mark/monochrome/white.svg"
              alt="fastui"
              className="size-6 shrink-0 hidden dark:block"
            />
            <img
              src="/assets/brand/wordmark/monochrome/black.svg"
              alt="fastui"
              className="h-4.5 w-auto dark:hidden object-contain"
            />
            <img
              src="/assets/brand/wordmark/monochrome/white.svg"
              alt="fastui"
              className="h-4.5 w-auto hidden dark:block object-contain"
            />
          </div>

          {/* Expanded Sidebar Collapse Toggle Button */}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              setOpen(false)
            }}
            className="flex items-center justify-center size-9 rounded-xl text-muted-foreground hover:text-foreground hover:bg-sidebar-accent transition-colors cursor-pointer"
            title="Collapse sidebar"
          >
            <PanelLeftClose className="size-5" />
          </button>
        </div>
      </SidebarHeader>


      {/* Nav */}
      <SidebarContent className="gap-0">
        <SidebarGroup className="px-1.5 pt-1 pb-0">
          <SidebarGroupContent>
            <SidebarMenu className="gap-1">
              {DESKTOP_NAV_ITEMS.map((item) => {
                const isActive = item.isActive(pathname)

                return (
                  <SidebarMenuItem key={item.id} className="flex justify-start w-full">

                    <SidebarMenuButton
                      asChild
                      isActive={isActive}
                      size="default"
                      tooltip={item.label}
                      className="group/nav-item h-10 w-full p-0 gap-0 text-sm font-normal rounded-xl justify-start overflow-hidden group-data-[collapsible=icon]:size-10!"
                    >
                      <Link
                        href={item.href}
                        className="flex items-center w-full h-full justify-start"
                        onClick={() => { if (isMobile) setOpenMobile(false) }}
                      >
                        {/* Fixed 40px icon column — same position in both expanded and collapsed */}
                        <div className="flex items-center justify-center size-10 shrink-0">
                          <item.icon
                            className="size-5 shrink-0 text-foreground"
                            strokeWidth={isActive ? 2 : 1.5}
                          />
                        </div>
                        {/* Text Label - hidden when icon-only */}
                        <span className="truncate pl-1 group-data-[collapsible=icon]:hidden text-foreground">
                          {item.label}
                        </span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      {/* Footer */}
      <SidebarFooter className="px-1.5 py-3">
        <SidebarMenu>
          <SidebarMenuItem className="flex justify-start w-full">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton
                  tooltip={displayName}
                  className="h-10 w-full p-0 gap-0 text-sm font-normal rounded-xl group/user justify-start overflow-hidden group-data-[collapsible=icon]:size-10! data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                >
                  {/* Fixed 40px avatar column — matches icon column position */}
                  <div className="flex items-center justify-center size-10 shrink-0">
                    <Avatar className="size-7 shrink-0 rounded-full after:rounded-full">
                      <AvatarFallback className="text-xs font-semibold bg-muted text-muted-foreground rounded-full">
                        {initials}
                      </AvatarFallback>
                    </Avatar>
                  </div>
                  <div className="flex flex-col min-w-0 flex-1 leading-none text-left pl-1 pr-2 group-data-[collapsible=icon]:hidden">
                    <span className="text-sm font-medium truncate">{displayName}</span>
                    <span className="text-xs text-muted-foreground truncate mt-0.5">{userEmail}</span>
                  </div>
                  <ChevronsUpDown className="ml-auto mr-2 size-4 shrink-0 text-muted-foreground group-data-[collapsible=icon]:hidden" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                side={side}
                align={align}
                sideOffset={8}
                className={cn(
                  state === "collapsed" && !isMobile ? "w-56" : "w-(--radix-dropdown-menu-trigger-width)"
                )}
              >
                <DropdownMenuGroup>
                  <DropdownMenuItem onClick={() => router.push("/settings")}>
                    <UserCircle className="size-4 shrink-0 text-muted-foreground" />
                    <span>Profile</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => router.push("/settings")}>
                    <Settings className="size-4 shrink-0 text-muted-foreground" />
                    <span>Settings</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}>
                    {resolvedTheme === "dark" ? (
                      <Sun className="size-4 shrink-0 text-muted-foreground" />
                    ) : (
                      <Moon className="size-4 shrink-0 text-muted-foreground" />
                    )}
                    <span>{resolvedTheme === "dark" ? "Light mode" : "Dark mode"}</span>
                  </DropdownMenuItem>
                </DropdownMenuGroup>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="size-4 shrink-0 text-muted-foreground" />
                  <span>Sign out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>

      <SidebarRail
        className={cn(
          "after:hidden",
          state === "collapsed"
            ? "cursor-col-resize hover:cursor-col-resize pointer-events-auto"
            : "cursor-default pointer-events-none"
        )}
        onClick={(e: React.MouseEvent) => {
          e.preventDefault()
          e.stopPropagation()
          setOpen(true)
        }}
      />
    </Sidebar>
  )
}
