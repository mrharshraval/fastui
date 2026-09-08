"use client"

import { Button } from "@/components/ui/button"
import { CheckCircle2 } from "lucide-react"
import { CTABanner } from "@/components/sections/cta-banner"

export default function Invisalign() {
    return (
        <main className="flex flex-col min-h-screen bg-background">
            {/* Hero Section */}
            <section className="w-full py-24 bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="flex flex-col gap-6 max-w-3xl">
                        <div className="inline-flex items-center rounded-full border bg-background px-3 py-1 text-sm font-medium text-muted-foreground border-border w-fit">
                            Invisalign® Provider
                        </div>
                        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none text-foreground">
                            The clear alternative to braces.
                        </h1>
                        <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl">
                            Straighten your teeth without interrupting your life. Invisalign aligners are virtually invisible, removable, and comfortable.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-4 pt-4">
                            <Button size="lg" className="rounded-full h-12 px-8 text-base font-medium">
                                Book Invisalign Consult
                            </Button>
                        </div>
                    </div>
                </div>
            </section>

            {/* How it Works */}
            <section className="w-full py-24 bg-background">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="mb-16">
                        <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl mb-4">How Invisalign Works</h2>
                        <p className="text-muted-foreground text-lg max-w-2xl">
                            A modern approach to straightening teeth using a custom-made series of aligners created for you and only you.
                        </p>
                    </div>
                    <div className="grid gap-8 md:grid-cols-3">
                        {[
                            {
                                step: "01",
                                title: "3D Scan",
                                desc: "We take a fast and precise digital scan of your teeth using our iTero scanner. No goopy impressions!"
                            },
                            {
                                step: "02",
                                title: "Custom Plan",
                                desc: "We map out the exact movements of your teeth and show you a preview of your new smile before you start."
                            },
                            {
                                step: "03",
                                title: "Start Smiling",
                                desc: "Wear your aligners 20-22 hours a day, changing to a new set every 1-2 weeks as your teeth gently move."
                            }
                        ].map((item, i) => (
                            <div key={i} className="bg-secondary/30 p-8 rounded-xl hover:bg-secondary/50 transition-colors group relative overflow-hidden">
                                <span className="absolute top-4 right-4 text-6xl font-bold text-muted-foreground/10 select-none">
                                    {item.step}
                                </span>
                                <h3 className="font-bold text-2xl mb-4 text-foreground relative z-10">{item.title}</h3>
                                <p className="text-muted-foreground leading-relaxed relative z-10">
                                    {item.desc}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Benefits vs Braces */}
            <section className="w-full py-24 bg-muted md:bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="grid gap-12 lg:grid-cols-2 items-center">
                        <div className="space-y-8">
                            <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">Why Choose Invisalign?</h2>
                            <div className="grid gap-6">
                                {[
                                    { title: "Virtually Invisible", desc: "Most people won't even notice you're wearing them." },
                                    { title: "Removable", desc: "Eat whatever you want and brush/floss normally." },
                                    { title: "Comfortable", desc: "Smooth plastic material causes less irritation than metal." },
                                    { title: "Fewer Visits", desc: "Check-ups are only needed every 6-8 weeks." }
                                ].map((benefit, i) => (
                                    <div key={i} className="flex gap-4">
                                        <div className="h-10 w-10 rounded-full bg-background flex items-center justify-center flex-none">
                                            <CheckCircle2 className="h-6 w-6 text-primary" />
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-lg">{benefit.title}</h3>
                                            <p className="text-muted-foreground">{benefit.desc}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="relative h-[500px] rounded-xl overflow-hidden bg-secondary/30 hidden lg:block">
                            {/* Placeholder for image */}
                            <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
                                Invisalign Smile Image
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA */}
            <CTABanner />
        </main>
    )
}
