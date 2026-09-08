"use client"

import { Button } from "@/components/ui/button"
import { CheckCircle2 } from "lucide-react"
import { CTABanner } from "@/components/sections/cta-banner"

export default function GeneralDentistry() {
    return (
        <main className="flex flex-col min-h-screen bg-background">
            {/* Hero Section */}
            <section className="w-full py-24 bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="flex flex-col items-center text-center md:items-start md:text-left gap-6 max-w-3xl mx-auto md:mx-0">
                        <div className="inline-flex items-center rounded-full border bg-background px-3 py-1 text-sm font-medium text-muted-foreground border-border w-fit">
                            General Dentistry
                        </div>
                        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none text-foreground text-center md:text-left">
                            The foundation of a healthy smile.
                        </h1>
                        <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl text-center md:text-left">
                            Preventive care and routine treatments to keep your teeth and gums healthy for life.
                        </p>
                        <div className="flex justify-center md:justify-start gap-4 pt-4 w-full">
                            <Button size="lg" className="rounded-full h-12 px-8 text-base font-medium">
                                Book Appointment
                            </Button>
                        </div>
                    </div>
                </div>
            </section>

            {/* Treatments Grid */}
            <section className="w-full py-24 bg-background">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="mb-16 text-center md:text-left">
                        <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl mb-4">Routine Care & Treatments</h2>
                        <p className="text-muted-foreground text-lg max-w-2xl mx-auto md:mx-0">
                            We recommend visiting us every six months for a checkup and cleaning to prevent issues before they start.
                        </p>
                    </div>
                    <div className="grid gap-8 md:grid-cols-3">
                        {[
                            {
                                title: "Exams & Cleanings",
                                desc: "Comprehensive exams, digital X-rays, and professional hygiene cleanings to remove plaque and tartar.",
                                features: ["Oral cancer screening", "Gum health check", "Polishing"]
                            },
                            {
                                title: "Fillings",
                                desc: "Tooth-colored composite fillings to repair cavities and restore the strength of your teeth.",
                                features: ["Mercury-free", "Natural look", "Durable"]
                            },
                            {
                                title: "Root Canals",
                                desc: "Therapy to save an infected tooth and relieve pain, avoiding the need for extraction.",
                                features: ["Pain relief", "Saves the tooth", "High success rate"]
                            }
                        ].map((item, i) => (
                            <div key={i} className="bg-secondary/30 p-8 rounded-xl hover:bg-secondary/50 transition-colors group flex flex-col items-center text-center md:items-start md:text-left">
                                <h3 className="font-bold text-2xl mb-4 text-foreground">{item.title}</h3>
                                <p className="text-muted-foreground mb-6 leading-relaxed">
                                    {item.desc}
                                </p>
                                <ul className="space-y-3 inline-block text-left">
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

            {/* CTA */}
            <CTABanner />
        </main>
    )
}
