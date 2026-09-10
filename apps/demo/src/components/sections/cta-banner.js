"use client"

import Image from "next/image"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { useDemo } from "@/lib/demo-context"

export function CTABanner({
    title = "Ready for your new smile?",
    description = "Book your consultation today and take the first step towards a healthier, confident smile.",
    buttonText = "Book Appointment",
    buttonHref = "/book"
}) {
    let demoLink = (href) => href
    try {
        const demo = useDemo()
        if (demo?.demoLink) {
            demoLink = demo.demoLink
        }
    } catch {
        // Outside demo provider fallback
    }

    const resolvedHref = demoLink(buttonHref)

    return (
        <section className="w-full py-12 md:py-16 bg-background">
            <div className="container px-4 sm:px-6 md:px-12 mx-auto">
                <div className="relative overflow-hidden rounded-3xl bg-primary text-primary-foreground px-6 py-14 md:py-16 text-center border border-primary/30">
                    {/* Flow Ribbon Background Image */}
                    <div className="absolute inset-0 overflow-hidden pointer-events-none">
                        <Image
                            src="/flow-ribbon.avif"
                            alt=""
                            fill
                            className="object-cover object-center pointer-events-none"
                            priority
                        />
                    </div>

                    <div className="relative z-10 max-w-xl mx-auto space-y-4">
                        <h2 className="text-2xl sm:text-3xl md:text-4xl font-semibold tracking-tight text-primary-foreground leading-tight">
                            {title}
                        </h2>
                        <p className="text-sm sm:text-base text-primary-foreground/90 font-normal leading-relaxed max-w-md mx-auto">
                            {description}
                        </p>
                        <div className="pt-2">
                            <Link href={resolvedHref}>
                                <Button
                                    size="lg"
                                    className="rounded-full h-11 px-8 text-sm font-semibold hover:scale-105 transition-all bg-primary-foreground text-primary hover:bg-primary-foreground/90 cursor-pointer"
                                >
                                    {buttonText}
                                </Button>
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    )
}
