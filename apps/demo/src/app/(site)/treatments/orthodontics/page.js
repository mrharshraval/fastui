"use client"

import { Button } from "@/components/ui/button"
import { CheckCircle2 } from "lucide-react"
import { CTABanner } from "@/components/sections/cta-banner"

export default function Orthodontics() {
    return (
        <main className="flex flex-col min-h-screen bg-background">
            {/* Hero Section */}
            <section className="w-full py-24 bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="flex flex-col gap-6 max-w-3xl">
                        <div className="inline-flex items-center rounded-full border bg-background px-3 py-1 text-sm font-medium text-muted-foreground border-border w-fit">
                            Orthodontics
                        </div>
                        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none text-foreground">
                            Straighten your smile with confidence.
                        </h1>
                        <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl">
                            Modern orthodontic solutions for children, teens, and adults. From clear aligners to traditional braces.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-4 pt-4">
                            <Button size="lg" className="rounded-full h-12 px-8 text-base font-medium">
                                Book Consultation
                            </Button>
                        </div>
                    </div>
                </div>
            </section>

            {/* Treatments Grid */}
            <section className="w-full py-24 bg-background">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="mb-16">
                        <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl mb-4">Our Orthodontic Options</h2>
                        <p className="text-muted-foreground text-lg max-w-2xl">
                            We use the latest technology to move teeth more efficiently and comfortably than ever before.
                        </p>
                    </div>
                    <div className="grid gap-8 md:grid-cols-3">
                        {[
                            {
                                title: "Invisalign®",
                                desc: "Clear, removable aligners that straighten your teeth without anyone knowing. Perfect for adults and teens.",
                                features: ["Virtually invisible", "Removable for eating", "Comfortable fit"]
                            },
                            {
                                title: "Traditional Braces",
                                desc: "High-grade metal brackets and wires that are smaller and more comfortable than ever before.",
                                features: ["Proven results", "Cost effective", "Fun color options"]
                            },
                            {
                                title: "Ceramic Braces",
                                desc: "Made of clear materials, these braces are less visible on your teeth than metal braces.",
                                features: ["Discreet appearance", "Stain resistant", "Effective movement"]
                            }
                        ].map((item, i) => (
                            <div key={i} className="bg-secondary/30 p-8 rounded-xl hover:bg-secondary/50 transition-colors group">
                                <h3 className="font-bold text-2xl mb-4 text-foreground">{item.title}</h3>
                                <p className="text-muted-foreground mb-6 leading-relaxed">
                                    {item.desc}
                                </p>
                                <ul className="space-y-3">
                                    {item.features.map((feature, j) => (
                                        <li key={j} className="flex items-center text-sm text-muted-foreground">
                                            <CheckCircle2 className="h-4 w-4 mr-2 text-primary" />
                                            {feature}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Benefits Section */}
            <section className="w-full py-24 bg-muted md:bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="grid gap-12 lg:grid-cols-2 items-center">
                        <div className="relative h-[500px] rounded-xl overflow-hidden bg-secondary/30 hidden lg:block order-2 lg:order-1">
                            {/* Placeholder for image */}
                            <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
                                Ortho Image
                            </div>
                        </div>
                        <div className="space-y-8 order-1 lg:order-2">
                            <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">Benefits of Straight Teeth</h2>
                            <p className="text-muted-foreground text-lg">
                                Orthodontics is about more than just a pretty smile. Properly aligned teeth are healthier and easier to maintain.
                            </p>
                            <div className="grid gap-6">
                                {[
                                    "Easier to clean and floss",
                                    "Reduced risk of gum disease",
                                    "Less wear and tear on teeth",
                                    "Improved chewing and speech",
                                    "Boosted self-confidence"
                                ].map((benefit, i) => (
                                    <div key={i} className="flex items-center gap-3">
                                        <div className="h-8 w-8 rounded-full bg-background flex items-center justify-center">
                                            <CheckCircle2 className="h-5 w-5 text-foreground" />
                                        </div>
                                        <span className="font-medium">{benefit}</span>
                                    </div>
                                ))}
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
