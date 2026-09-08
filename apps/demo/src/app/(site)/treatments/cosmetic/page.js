"use client"

import { Button } from "@/components/ui/button"
import { CheckCircle2, ArrowRight } from "lucide-react"
import Link from "next/link"
import { CTABanner } from "@/components/sections/cta-banner"

export default function CosmeticDentistry() {
    return (
        <main className="flex flex-col min-h-screen bg-background">
            {/* Hero Section */}
            <section className="w-full py-24 bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="flex flex-col gap-6 max-w-3xl">
                        <div className="inline-flex items-center rounded-full border bg-background px-3 py-1 text-sm font-medium text-muted-foreground border-border w-fit">
                            Cosmetic Dentistry
                        </div>
                        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none text-foreground">
                            Design your perfect smile.
                        </h1>
                        <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl">
                            From subtle changes to major repairs, our cosmetic treatments can improve your smile and boost your confidence.
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
                        <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl mb-4">Our Cosmetic Solutions</h2>
                        <p className="text-muted-foreground text-lg max-w-2xl">
                            We offer a comprehensive range of aesthetic treatments tailored to your unique facial structure and desires.
                        </p>
                    </div>
                    <div className="grid gap-8 md:grid-cols-3">
                        {[
                            {
                                title: "Porcelain Veneers",
                                desc: "Thin, custom-made shells designed to cover the front surface of teeth to improve your appearance.",
                                features: ["Stain resistant", "Natural look", "Long lasting"]
                            },
                            {
                                title: "Professional Whitening",
                                desc: "Powerful whitening treatments that can brighten your smile by several shades in just one visit.",
                                features: ["Immediate results", "Safe & effective", "Custom trays"]
                            },
                            {
                                title: "Dental Bonding",
                                desc: "A durable plastic material is applied and hardened with a special light to repair decayed or chipped teeth.",
                                features: ["Cost effective", "Single visit", "Minimally invasive"]
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

            {/* Process Section */}
            <section className="w-full py-24 bg-muted md:bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="grid gap-12 lg:grid-cols-2 items-center">
                        <div className="space-y-8">
                            <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">Your Smile Makeover Journey</h2>
                            <div className="space-y-8">
                                {[
                                    { step: "01", title: "Consultation", desc: "We discuss your goals and analyze your smile using digital imaging." },
                                    { step: "02", title: "Design", desc: "We create a custom treatment plan and show you a preview of your new smile." },
                                    { step: "03", title: "Transformation", desc: "Our specialists perform the treatments with precision and care." }
                                ].map((step, i) => (
                                    <div key={i} className="flex gap-6">
                                        <div className="flex-none">
                                            <span className="text-3xl font-bold text-muted-foreground/20">{step.step}</span>
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-xl mb-2">{step.title}</h3>
                                            <p className="text-muted-foreground leading-relaxed">{step.desc}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="relative h-[500px] rounded-xl overflow-hidden bg-secondary/30 hidden lg:block">
                            {/* Placeholder for process image */}
                            <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
                                Process Image
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
