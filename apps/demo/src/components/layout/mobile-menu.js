"use client"

import * as React from "react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { siteConfig } from "@/config/site"
import { Button } from "@/components/ui/button"
import { useDemo } from "@/lib/demo-context"
import {
    ChevronDown,
    X,
} from "lucide-react"
import { Icons } from "@/components/icons"
import { ThemeToggle } from "@/components/layout/theme-toggle"

export function MobileMenu({ setOpen }) {
    const [treatmentsOpen, setTreatmentsOpen] = React.useState(true)
    const { business, demoLink } = useDemo()
    const clinicName = business?.name || siteConfig.name

    return (
        <div className="flex flex-col h-full bg-background">
            {/* Header with Logo and Close Button - Matches Navbar Height (72px) */}
            <div className="flex h-[72px] items-center justify-between px-4 border-b border-border/40">
                <Link href={demoLink("/")} className="flex items-center space-x-2" onClick={() => setOpen(false)}>
                    {business?.logo_url ? (
                        <img
                            src={business.logo_url}
                            alt={clinicName}
                            className="h-7 max-w-[140px] object-contain"
                            referrerPolicy="no-referrer"
                        />
                    ) : (
                        <>
                            <Icons.logo className="h-6 w-auto text-primary" />
                            <span className="font-bold text-lg tracking-tight">{clinicName}</span>
                        </>
                    )}
                </Link>
                <div className="flex items-center space-x-2">
                    <ThemeToggle />
                    <button
                        onClick={() => setOpen(false)}
                        className="rounded-full p-2 opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 hover:bg-muted"
                    >
                        <X className="h-5 w-5" />
                        <span className="sr-only">Close</span>
                    </button>
                </div>
            </div>

            {/* Navigation Links */}
            <nav className="flex flex-col space-y-1 px-4 py-6 overflow-y-auto no-scrollbar text-left">
                <Link
                    href={demoLink("/")}
                    className="flex w-full items-center justify-start rounded-lg py-2.5 px-3 text-sm font-medium transition-colors hover:bg-muted hover:text-primary"
                    onClick={() => setOpen(false)}
                >
                    Home
                </Link>

                {/* Treatments Accordion */}
                <div className="py-1 w-full flex flex-col">
                    <button
                        onClick={() => setTreatmentsOpen(!treatmentsOpen)}
                        className="flex w-full items-center justify-between rounded-lg py-2.5 px-3 text-sm font-medium transition-colors hover:bg-muted hover:text-primary group"
                    >
                        <span>Treatments</span>
                        <ChevronDown
                            className={cn(
                                "h-4 w-4 text-muted-foreground transition-transform duration-200",
                                treatmentsOpen ? "rotate-180" : ""
                            )}
                        />
                    </button>
                    {treatmentsOpen && (
                        <div className="flex flex-col space-y-1 pl-3 pt-1 pb-2 w-full border-l-2 border-border/60 ml-3 animate-in slide-in-from-top-1 fade-in duration-200">
                            <Link
                                href={demoLink("/treatments/general")}
                                className="flex w-full items-center justify-start rounded-lg py-2 px-3 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
                                onClick={() => setOpen(false)}
                            >
                                General Dentistry
                            </Link>
                            <Link
                                href={demoLink("/treatments/cosmetic")}
                                className="flex w-full items-center justify-start rounded-lg py-2 px-3 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
                                onClick={() => setOpen(false)}
                            >
                                Cosmetic Dentistry
                            </Link>
                            <Link
                                href={demoLink("/treatments/orthodontics")}
                                className="flex w-full items-center justify-start rounded-lg py-2 px-3 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
                                onClick={() => setOpen(false)}
                            >
                                Orthodontics
                            </Link>
                            <Link
                                href={demoLink("/treatments/surgical")}
                                className="flex w-full items-center justify-start rounded-lg py-2 px-3 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
                                onClick={() => setOpen(false)}
                            >
                                Surgical
                            </Link>
                            <Link
                                href={demoLink("/treatments/implants")}
                                className="flex w-full items-center justify-start rounded-lg py-2 px-3 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
                                onClick={() => setOpen(false)}
                            >
                                Dental Implants
                            </Link>
                            <Link
                                href={demoLink("/treatments/pediatric")}
                                className="flex w-full items-center justify-start rounded-lg py-2 px-3 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
                                onClick={() => setOpen(false)}
                            >
                                Pediatric Dentistry
                            </Link>
                        </div>
                    )}
                </div>

                <Link
                    href={demoLink("/gallery")}
                    className="flex w-full items-center justify-start rounded-lg py-2.5 px-3 text-sm font-medium transition-colors hover:bg-muted hover:text-primary"
                    onClick={() => setOpen(false)}
                >
                    Gallery
                </Link>
                <Link
                    href={demoLink("/insurance")}
                    className="flex w-full items-center justify-start rounded-lg py-2.5 px-3 text-sm font-medium transition-colors hover:bg-muted hover:text-primary"
                    onClick={() => setOpen(false)}
                >
                    Insurance
                </Link>

                <Link
                    href={demoLink("/about")}
                    className="flex w-full items-center justify-start rounded-lg py-2.5 px-3 text-sm font-medium transition-colors hover:bg-muted hover:text-primary"
                    onClick={() => setOpen(false)}
                >
                    About
                </Link>
                <Link
                    href={demoLink("/contact")}
                    className="flex w-full items-center justify-start rounded-lg py-2.5 px-3 text-sm font-medium transition-colors hover:bg-muted hover:text-primary"
                    onClick={() => setOpen(false)}
                >
                    Contact Us
                </Link>
            </nav>

            {/* Footer / CTA */}
            <div className="mt-auto px-4 pb-8 flex justify-center">
                <Link href={demoLink("/book")} onClick={() => setOpen(false)} className="w-full block">
                    <Button className="w-full justify-center rounded-full bg-primary text-primary-foreground hover:bg-primary/90 h-10 text-sm font-medium shadow-sm transition-all hover:scale-105">
                        Book appointment
                    </Button>
                </Link>
            </div>
        </div>
    )
}
