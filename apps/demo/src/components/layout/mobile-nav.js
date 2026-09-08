"use client"

import * as React from "react"
import Link from "next/link"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
    Sheet,
    SheetContent,
    SheetTrigger,
} from "@/components/ui/sheet"
import { Icons } from "@/components/icons"

export function MobileNav() {
    const [open, setOpen] = React.useState(false)

    return (
        <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
                <Button
                    variant="ghost"
                    className="px-0 text-base hover:bg-transparent focus-visible:bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0 md:hidden"
                >
                    <Icons.menu className="h-6 w-6" />
                    <span className="sr-only">Toggle Menu</span>
                </Button>
            </SheetTrigger>
            <SheetContent side="right" className="pr-0">
                <MobileLink
                    href="/"
                    className="flex items-center"
                    onOpenChange={setOpen}
                >
                    <span className="font-bold">Brainlab</span>
                </MobileLink>
                <div className="my-4 h-[calc(100vh-8rem)] pb-10 pl-6 pr-6">
                    <div className="relative mb-4">
                        <Icons.search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input placeholder="Search treatment..." className="pl-8 rounded-full bg-muted/50" />
                    </div>
                    <div className="flex flex-col space-y-4 items-center text-center">
                        <MobileLink href="/" onOpenChange={setOpen} className="text-center">
                            Home
                        </MobileLink>
                        <MobileLink href="/treatments" onOpenChange={setOpen} className="text-center">
                            Treatments
                        </MobileLink>
                        <MobileLink href="/about" onOpenChange={setOpen} className="text-center">
                            About
                        </MobileLink>
                        <MobileLink href="/contact" onOpenChange={setOpen} className="text-center">
                            Contact Us
                        </MobileLink>
                        <div className="pt-4 mt-4 border-t w-full flex justify-center">
                            <Button className="w-full rounded-full bg-black text-white hover:bg-black/90">
                                Book appointment
                            </Button>
                        </div>
                    </div>
                </div>
            </SheetContent>
        </Sheet>
    )
}

function MobileLink({ href, onOpenChange, className, children, ...props }) {
    const router = require("next/navigation").useRouter()
    return (
        <Link
            href={href}
            onClick={() => {
                router.push(href)
                onOpenChange?.(false)
            }}
            className={cn(
                "text-foreground/70 transition-colors hover:text-foreground",
                className
            )}
            {...props}
        >
            {children}
        </Link>
    )
}
