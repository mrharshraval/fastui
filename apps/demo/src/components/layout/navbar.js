"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import { cn } from "@/lib/utils"
import { Icons } from "@/components/icons"
import { Button } from "@/components/ui/button"
import { MobileMenu } from "@/components/layout/mobile-menu"
import { CommandMenu } from "@/components/layout/command-menu"
import { ThemeToggle } from "@/components/layout/theme-toggle"
import { siteConfig } from "@/config/site"
import { useDemo } from "@/lib/demo-context"
import {
    Sheet,
    SheetContent,
    SheetTrigger,
    SheetTitle,
    SheetDescription,
} from "@/components/ui/sheet"
import {
    NavigationMenu,
    NavigationMenuContent,
    NavigationMenuItem,
    NavigationMenuLink,
    NavigationMenuList,
    NavigationMenuTrigger,
    navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu"
import { Asterisk, ArrowRight } from "lucide-react"

export function Navbar() {
    const [open, setOpen] = React.useState(false) // Search dialog
    const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false)
    const [scrolled, setScrolled] = React.useState(false)
    const [currentNavItem, setCurrentNavItem] = React.useState("")
    const pathname = usePathname()
    const { business, demoLink } = useDemo()
    const clinicName = business?.name || siteConfig.name

    React.useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20)
        }
        window.addEventListener("scroll", handleScroll)
        return () => window.removeEventListener("scroll", handleScroll)
    }, [])

    return (
        <header className={cn(
            "sticky top-0 z-50 w-full transition-all duration-300",
            scrolled ? "bg-background/80 backdrop-blur-md supports-[backdrop-filter]:bg-background/60 border-b border-border shadow-xs" : "bg-transparent"
        )}>
            <CommandMenu open={open} setOpen={setOpen} />

            <div className="container flex h-[72px] md:h-[96px] px-8 sm:px-4 md:px-12 items-center justify-between">

                {/* Logo (Desktop & Mobile) */}
                <div className="flex items-center">
                    <Link href={demoLink("/")} className="mr-6 flex items-center space-x-2">
                        {business?.logo_url ? (
                            <img
                                src={business.logo_url}
                                alt={clinicName}
                                className="h-7 max-w-[140px] object-contain"
                                referrerPolicy="no-referrer"
                            />
                        ) : (
                            <>
                                <Asterisk className="h-6 w-6" />
                                <span className="hidden font-bold sm:inline-block">
                                    {clinicName}
                                </span>
                            </>
                        )}
                    </Link>

                    {/* Desktop Nav */}
                    <div className="hidden md:flex items-center gap-1">
                        <NavigationMenu value={currentNavItem} onValueChange={setCurrentNavItem}>
                            <NavigationMenuList>
                                <NavigationMenuItem>
                                    <NavigationMenuLink asChild>
                                        <Link
                                            href={demoLink("/")}
                                            className={cn(
                                                navigationMenuTriggerStyle(),
                                                "h-9 rounded-full px-4 text-sm font-medium transition-colors hover:bg-muted hover:text-foreground focus:bg-muted focus:text-foreground bg-transparent",
                                                (pathname === demoLink("/") || pathname === "/") && "bg-muted text-foreground"
                                            )}
                                        >
                                            Home
                                        </Link>
                                    </NavigationMenuLink>
                                </NavigationMenuItem>

                                <NavigationMenuItem value="treatments">
                                    <NavigationMenuTrigger
                                        onClick={(e) => {
                                            if (currentNavItem === "treatments") {
                                                e.preventDefault()
                                            }
                                        }}
                                        className={cn(
                                            "group inline-flex h-9 w-max items-center justify-center rounded-full px-4 text-sm font-medium transition-colors",
                                            "hover:bg-muted hover:text-foreground",
                                            "bg-transparent",
                                            "data-[state=open]:bg-muted data-[active]:bg-muted",
                                            "focus:outline-none",
                                            pathname?.includes("/treatments") && "bg-muted text-foreground"
                                        )}
                                    >
                                        Treatments
                                    </NavigationMenuTrigger>
                                    <NavigationMenuContent>
                                        <ul className="grid w-[600px] grid-cols-2 gap-2 p-4">
                                            <ListItem href={demoLink("/treatments/general")} title="General Dentistry">
                                                Checkups, cleanings & exams
                                            </ListItem>
                                            <ListItem href={demoLink("/treatments/pediatric")} title="Pediatric">
                                                Gentle care for kids & teens
                                            </ListItem>
                                            <ListItem href={demoLink("/treatments/surgical")} title="Surgical">
                                                Extractions & oral surgery
                                            </ListItem>
                                            <ListItem href={demoLink("/treatments/cosmetic")} title="Cosmetic">
                                                Whitening, veneers & bonding
                                            </ListItem>
                                            <ListItem href={demoLink("/treatments/orthodontics")} title="Orthodontics">
                                                Braces & clear aligners
                                            </ListItem>
                                            <ListItem href={demoLink("/treatments/implants")} title="Dental Implants">
                                                Solutions for missing teeth
                                            </ListItem>
                                        </ul>
                                    </NavigationMenuContent>
                                </NavigationMenuItem>

                                <NavigationMenuItem>
                                    <NavigationMenuLink asChild>
                                        <Link
                                            href={demoLink("/about")}
                                            className={cn(
                                                navigationMenuTriggerStyle(),
                                                "h-9 rounded-full px-4 text-sm font-medium transition-colors hover:bg-muted hover:text-foreground focus:bg-muted focus:text-foreground bg-transparent",
                                                pathname?.includes("/about") && "bg-muted text-foreground"
                                            )}
                                        >
                                            About
                                        </Link>
                                    </NavigationMenuLink>
                                </NavigationMenuItem>

                                <NavigationMenuItem>
                                    <NavigationMenuLink asChild>
                                        <Link
                                            href={demoLink("/gallery")}
                                            className={cn(
                                                navigationMenuTriggerStyle(),
                                                "h-9 rounded-full px-4 text-sm font-medium transition-colors hover:bg-muted hover:text-foreground focus:bg-muted focus:text-foreground bg-transparent",
                                                pathname?.includes("/gallery") && "bg-muted text-foreground"
                                            )}
                                        >
                                            Gallery
                                        </Link>
                                    </NavigationMenuLink>
                                </NavigationMenuItem>

                                <NavigationMenuItem>
                                    <NavigationMenuLink asChild>
                                        <Link
                                            href={demoLink("/insurance")}
                                            className={cn(
                                                navigationMenuTriggerStyle(),
                                                "h-9 rounded-full px-4 text-sm font-medium transition-colors hover:bg-muted hover:text-foreground focus:bg-muted focus:text-foreground bg-transparent",
                                                pathname?.includes("/insurance") && "bg-muted text-foreground"
                                            )}
                                        >
                                            Insurance
                                        </Link>
                                    </NavigationMenuLink>
                                </NavigationMenuItem>

                                <NavigationMenuItem>
                                    <NavigationMenuLink asChild>
                                        <Link
                                            href={demoLink("/contact")}
                                            className={cn(
                                                navigationMenuTriggerStyle(),
                                                "h-9 rounded-full px-4 text-sm font-medium transition-colors hover:bg-muted hover:text-foreground focus:bg-muted focus:text-foreground bg-transparent",
                                                pathname?.includes("/contact") && "bg-muted text-foreground"
                                            )}
                                        >
                                            Contact
                                        </Link>
                                    </NavigationMenuLink>
                                </NavigationMenuItem>
                            </NavigationMenuList>
                        </NavigationMenu>
                    </div>
                </div>

                {/* Right Side Actions */}
                <div className="flex items-center space-x-2 sm:space-x-3">
                    {/* Theme Toggle */}
                    <ThemeToggle />

                    {/* Search (Desktop & Mobile) - Hidden for now */}
                    <div className="w-auto hidden">
                        <Button
                            variant="outline"
                            className="relative h-8 w-full justify-start rounded-full bg-background text-sm font-normal text-muted-foreground shadow-none sm:pr-12 md:w-40 lg:w-64"
                            onClick={() => setOpen(true)}
                        >
                            <span className="hidden lg:inline-flex">Search treatments...</span>
                            <span className="inline-flex lg:hidden">Search...</span>
                            <kbd className="pointer-events-none absolute right-1.5 top-1/2 -translate-y-1/2 hidden h-5 select-none items-center gap-1 rounded-full border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex">
                                <span className="text-xs">Ctrl</span>K
                            </kbd>
                        </Button>
                    </div>

                    {/* Book Appointment (Desktop Only) */}
                    <Link href={demoLink("/book")}>
                        <Button className="hidden md:inline-flex h-9 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 px-5 text-sm font-medium shadow-sm transition-all hover:scale-105">
                            Book appointment
                        </Button>
                    </Link>

                    {/* Mobile Menu Trigger (Sheet) */}
                    <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
                        <SheetTrigger asChild>
                            <Button
                                variant="ghost"
                                className="px-0 text-base hover:bg-transparent focus-visible:bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 md:hidden"
                            >
                                <Icons.menu className="h-5 w-5" />
                                <span className="sr-only">Toggle Menu</span>
                            </Button>
                        </SheetTrigger>
                        <SheetContent side="right" className="p-0 [&>button]:hidden">
                            <SheetTitle className="sr-only">Mobile Menu</SheetTitle>
                            <SheetDescription className="sr-only">Navigation menu for mobile devices</SheetDescription>
                            <MobileMenu setOpen={setMobileMenuOpen} />
                        </SheetContent>
                    </Sheet>
                </div>
            </div>
        </header>
    )
}

const ListItem = React.forwardRef(({ className, title, children, href, ...props }, ref) => {
    return (
        <li>
            <NavigationMenuLink asChild>
                <Link
                    ref={ref}
                    href={href || "#"}
                    className={cn(
                        "group flex select-none items-center justify-between gap-4 rounded-md p-3 leading-none no-underline outline-none transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground",
                        className
                    )}
                    {...props}
                >
                    <div className="space-y-1">
                        <div className="text-sm font-medium leading-none">{title}</div>
                        <p className="truncate text-sm text-muted-foreground w-[200px]">
                            {children}
                        </p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground/70 group-hover:text-primary transition-colors" />
                </Link>
            </NavigationMenuLink>
        </li>
    )
})
ListItem.displayName = "ListItem"
