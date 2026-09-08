"use client"

import { Button } from "@/components/ui/button"
import { CheckCircle2 } from "lucide-react"
import { CTABanner } from "@/components/sections/cta-banner"

export default function PediatricDentistry() {
    return (
        <main className="flex flex-col min-h-screen bg-background">
            {/* Hero Section */}
            <section className="w-full py-24 bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="flex flex-col gap-6 max-w-3xl">
                        <div className="inline-flex items-center rounded-full border bg-background px-3 py-1 text-sm font-medium text-muted-foreground border-border w-fit">
                            Pediatric Dentistry
                        </div>
                        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none text-foreground">
                            Gentle care for growing smiles.
                        </h1>
                        <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl">
                            We create a fun, safe, and positive dental experience for children of all ages, from infants to teens.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-4 pt-4">
                            <Button size="lg" className="rounded-full h-12 px-8 text-base font-medium">
                                Book Kids Appointment
                            </Button>
                        </div>
                    </div>
                </div>
            </section>

            {/* Treatments Grid */}
            <section className="w-full py-24 bg-background">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="mb-16">
                        <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl mb-4">Kids Dental Services</h2>
                        <p className="text-muted-foreground text-lg max-w-2xl">
                            Our team is trained to handle the unique needs of children, focusing on prevention and education.
                        </p>
                    </div>
                    <div className="grid gap-8 md:grid-cols-3">
                        {[
                            {
                                title: "First Visit",
                                desc: "A happy introduction to the dentist. We count teeth, check gums, and make it a fun adventure.",
                                features: ["Age 1 or first tooth", "Parent education", "No fear approach"]
                            },
                            {
                                title: "Sealants & Fluoride",
                                desc: "Protective coatings and treatments to strengthen enamel and prevent cavities in hard-to-reach areas.",
                                features: ["Prevents decay", "Quick application", "Pain-free"]
                            },
                            {
                                title: "Early Orthodontics",
                                desc: "Monitoring jaw growth and tooth development to identify potential issues early on.",
                                features: ["Growth tracking", "Space maintenance", "Habit correction"]
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

            {/* CTA */}
            <CTABanner />
        </main>
    )
}
