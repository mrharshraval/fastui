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
        // Floating fixed position with iOS safe-area clearance
        "fixed bottom-[max(0.9rem,env(safe-area-inset-bottom))] inset-x-0 mx-auto z-40",
        "w-[calc(100%-2.5rem)] max-w-[340px]",
        // Highly Translucent Liquid Glass Material (25-30% lighter base fill)
        "bg-background/40 dark:bg-[#101014]/45",
        "backdrop-blur-3xl backdrop-saturate-[190%]",
        "border border-border/25 dark:border-white/[0.06]",
        // Layered spatial depth shadow
        "shadow-[0_12px_36px_-4px_rgba(0,0,0,0.10),0_4px_12px_-2px_rgba(0,0,0,0.04)]",
        "dark:shadow-[0_18px_44px_-6px_rgba(0,0,0,0.60),0_6px_16px_-2px_rgba(0,0,0,0.35)]",
        // Uniform concentric padding (exact 6px padding on all sides)
        "rounded-full p-1.5",
        "block md:hidden",
        "transition-all duration-200"
      )}
    >
      <div className="grid grid-cols-5 items-center gap-1 w-full m-0 p-0">
        {MOBILE_NAV_ITEMS.map((item: NavItem) => {
          const isActive = item.isActive(pathname)
          const isDiscover = item.id === "discover"
          const Icon = item.icon

          return (
            <Link
              key={item.id}
              href={item.href}
              aria-label={item.label}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "relative flex items-center justify-center h-10 w-full rounded-full cursor-pointer select-none transition-all duration-200",
                isActive
                  ? "bg-neutral-200/50 dark:bg-white/[0.08] text-foreground"
                  : "text-muted-foreground/60 hover:text-foreground hover:bg-black/[0.03] dark:hover:bg-white/[0.04] active:scale-90"
              )}
            >
              <Icon
                size={isDiscover ? 21 : 19}
                className={cn(
                  "shrink-0 transition-all duration-150",
                  isActive
                    ? "text-foreground opacity-100"
                    : "text-muted-foreground/60 opacity-60 hover:opacity-100 hover:text-foreground"
                )}
                strokeWidth={isActive ? 2.2 : 1.65}
              />
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
