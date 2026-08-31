import {
  LayoutDashboard,
  Compass,
  UserSearch,
  Users,
  UserCircle,
  type LucideIcon,
} from "lucide-react"

export interface NavItem {
  id: string
  label: string
  icon: LucideIcon
  href: string
  isActive: (pathname: string) => boolean
}

export const NAV_DESTINATIONS: Record<string, NavItem> = {
  home: {
    id: "home",
    label: "Home",
    icon: LayoutDashboard,
    href: "/",
    isActive: (pathname: string) => pathname === "/",
  },
  discover: {
    id: "discover",
    label: "Discover",
    icon: Compass,
    href: "/discover",
    isActive: (pathname: string) => pathname.startsWith("/discover") || pathname.startsWith("/prospecting"),
  },
  prospects: {
    id: "prospects",
    label: "Prospects",
    icon: UserSearch,
    href: "/prospects",
    isActive: (pathname: string) => pathname.startsWith("/prospects"),
  },
  leads: {
    id: "leads",
    label: "Leads",
    icon: Users,
    href: "/leads",
    isActive: (pathname: string) => pathname.startsWith("/leads"),
  },
  user: {
    id: "user",
    label: "Account",
    icon: UserCircle,
    href: "/settings",
    isActive: (pathname: string) => pathname.startsWith("/settings") || pathname.startsWith("/profile"),
  },
}

// Desktop Sidebar order: Home -> Discover -> Prospects -> Leads (User in sidebar footer)
export const DESKTOP_NAV_ITEMS: NavItem[] = [
  NAV_DESTINATIONS.home,
  NAV_DESTINATIONS.discover,
  NAV_DESTINATIONS.prospects,
  NAV_DESTINATIONS.leads,
]

// Mobile Bottom Nav order: Home -> Prospects -> Discover (CENTER) -> Leads -> User
export const MOBILE_NAV_ITEMS: NavItem[] = [
  NAV_DESTINATIONS.home,
  NAV_DESTINATIONS.prospects,
  NAV_DESTINATIONS.discover,
  NAV_DESTINATIONS.leads,
  NAV_DESTINATIONS.user,
]
