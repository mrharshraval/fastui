"use client"

import { Button } from "@/components/ui/button"
import { CheckCircle2, Phone } from "lucide-react"
import { CTABanner } from "@/components/sections/cta-banner"

export default function EmergencyDentistry() {
    return (
        <main className="flex flex-col min-h-screen bg-background">
            {/* Hero Section */}
            <section className="w-full py-24 bg-red-50/50 dark:bg-red-950/10">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="flex flex-col gap-6 max-w-3xl">
                        <div className="inline-flex items-center rounded-full border bg-background px-3 py-1 text-sm font-medium text-red-600 border-red-200 w-fit">
                            Emergency Care
                        </div>
                        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none text-foreground">
                            In pain? We can help today.
                        </h1>
                        <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl">
                            We offer same-day emergency appointments for toothaches, broken teeth, and other urgent dental needs.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-4 pt-4">
                            <Button size="lg" className="rounded-full h-12 px-8 text-base font-medium bg-red-600 hover:bg-red-700 text-white border-none">
                                <Phone className="mr-2 h-4 w-4" /> Call Now: (555) 123-4567
                            </Button>
                        </div>
                    </div>
                </div>
            </section>

            {/* What is an Emergency? */}
            <section className="w-full py-24 bg-background">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="mb-16">
                        <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl mb-4">Common Dental Emergencies</h2>
                        <p className="text-muted-foreground text-lg max-w-2xl">
                            If you are experiencing any of the following, please contact us immediately.
                        </p>
                    </div>
                    <div className="grid gap-8 md:grid-cols-3">
                        {[
                            {
                                title: "Severe Toothache",
                                desc: "Persistent, throbbing pain can indicate an infection that needs immediate treatment.",
                                action: "Rinse with warm water and floss gently."
                            },
                            {
                                title: "Knocked-Out Tooth",
                                desc: "Time is critical. We may be able to save the tooth if you see us within an hour.",
                                action: "Keep the tooth moist in milk or saliva."
                            },
                            {
                                title: "Broken or Chipped Tooth",
                                desc: "Can cause pain and lead to further damage or infection if left untreated.",
                                action: "Save any broken pieces if possible."
                            },
                            {
                                title: "Lost Filling or Crown",
                                desc: "Exposes the sensitive inner tooth structure and can be painful.",
                                action: "Use dental cement or sugar-free gum as a temporary fix."
                            },
                            {
                                title: "Abscess or Swelling",
                                desc: "A sign of serious infection that can spread to other parts of the body.",
                                action: "Do not pop the abscess. Call us immediately."
                            },
                            {
                                title: "Bleeding Gums",
                                desc: "Uncontrolled bleeding after an extraction or injury requires urgent care.",
                                action: "Apply firm pressure with clean gauze."
                            }
                        ].map((item, i) => (
                            <div key={i} className="bg-secondary/30 p-8 rounded-xl hover:bg-secondary/50 transition-colors group">
                                <h3 className="font-bold text-2xl mb-4 text-foreground">{item.title}</h3>
                                <p className="text-muted-foreground mb-4 leading-relaxed">
                                    {item.desc}
                                </p>
                                <div className="text-sm font-medium text-primary bg-primary/10 p-3 rounded-lg inline-block">
                                    Tip: {item.action}
                                </div>
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
