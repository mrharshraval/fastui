"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { MOBILE_NAV_ITEMS, NavItem } from "@/config/navigation"
import { cn } from "@/lib/utils"

export function MobileBottomNav() {
  const pathname = usePathname()

  return (
    <nav
      aria-label="Mobile Navigation"
      className={cn(
        "fixed bottom-0 inset-x-0 z-40 block md:hidden",
        "bg-background/50 dark:bg-background/45",
        "backdrop-blur-2xl backdrop-saturate-150",
        "border-t border-border/25 dark:border-white/10",
        "shadow-[0_-4px_20px_rgba(0,0,0,0.03)] dark:shadow-[0_-4px_20px_rgba(0,0,0,0.3)]",
        "pb-[env(safe-area-inset-bottom)]"
      )}
    >
      <div className="flex items-center justify-around h-14 max-w-md mx-auto px-4">
        {MOBILE_NAV_ITEMS.map((item: NavItem) => {
          const isActive = item.isActive(pathname)
          const Icon = item.icon
          const isCenter = item.id === "discover"

          return (
            <Link
              key={item.id}
              href={item.href}
              aria-label={item.label}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "relative flex items-center justify-center size-11 select-none transition-all duration-150 cursor-pointer active:scale-90",
                isActive
                  ? "text-foreground"
                  : "text-muted-foreground/70 hover:text-foreground"
              )}
            >
              <Icon
                size={isCenter ? 24 : 22}
                className={cn(
                  "shrink-0 transition-all duration-150",
                  isActive ? "text-foreground stroke-[2.35]" : "text-muted-foreground stroke-[1.8]"
                )}
              />
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
