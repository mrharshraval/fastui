"use client"

import { Button } from "@/components/ui/button"
import { CheckCircle2 } from "lucide-react"
import { CTABanner } from "@/components/sections/cta-banner"

export default function SurgicalDentistry() {
    return (
        <main className="flex flex-col min-h-screen bg-background">
            {/* Hero Section */}
            <section className="w-full py-24 bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="flex flex-col gap-6 max-w-3xl">
                        <div className="inline-flex items-center rounded-full border bg-background px-3 py-1 text-sm font-medium text-muted-foreground border-border w-fit">
                            Oral Surgery
                        </div>
                        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none text-foreground">
                            Expert surgical care in a comfortable setting.
                        </h1>
                        <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl">
                            From wisdom teeth removal to complex reconstructive surgery, our specialists ensure a safe and pain-free experience.
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
                        <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl mb-4">Surgical Procedures</h2>
                        <p className="text-muted-foreground text-lg max-w-2xl">
                            We use advanced sedation techniques and minimally invasive methods to ensure your comfort and quick recovery.
                        </p>
                    </div>
                    <div className="grid gap-8 md:grid-cols-3">
                        {[
                            {
                                title: "Wisdom Teeth Removal",
                                desc: "Safe extraction of impacted or problematic wisdom teeth to prevent pain and overcrowding.",
                                features: ["Sedation options", "Quick recovery", "Expert care"]
                            },
                            {
                                title: "Dental Extractions",
                                desc: "Removal of severely decayed or damaged teeth that cannot be saved by other means.",
                                features: ["Pain management", "Bone preservation", "Replacement planning"]
                            },
                            {
                                title: "Bone Grafting",
                                desc: "Restoring bone density in the jaw to prepare for dental implants or repair defects.",
                                features: ["Advanced materials", "Foundation for implants", "Tissue regeneration"]
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

            {/* Sedation Section */}
            <section className="w-full py-24 bg-muted md:bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="grid gap-12 lg:grid-cols-2 items-center">
                        <div className="space-y-8">
                            <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">Anxiety-Free Dentistry</h2>
                            <p className="text-muted-foreground text-lg">
                                We understand that surgery can be stressful. That's why we offer multiple sedation options to ensure you are completely relaxed.
                            </p>
                            <div className="grid gap-6">
                                {[
                                    { title: "Nitrous Oxide", desc: "Mild sedation ('laughing gas') to help you relax." },
                                    { title: "Oral Sedation", desc: "A pill taken before the appointment for deeper relaxation." },
                                    { title: "IV Sedation", desc: "Controlled sedation for maximum comfort during complex procedures." }
                                ].map((option, i) => (
                                    <div key={i} className="bg-background p-6 rounded-xl">
                                        <h3 className="font-bold text-lg mb-2">{option.title}</h3>
                                        <p className="text-muted-foreground text-sm">{option.desc}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="relative h-[500px] rounded-xl overflow-hidden bg-secondary/30 hidden lg:block">
                            {/* Placeholder for image */}
                            <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
                                Sedation Image
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
