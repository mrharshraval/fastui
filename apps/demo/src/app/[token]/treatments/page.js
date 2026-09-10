"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Sparkles, Smile, Hammer, Stethoscope, ArrowRight, HeartPulse } from "lucide-react"
import { useDemo } from "@/lib/demo-context"
import { CTABanner } from "@/components/sections/cta-banner"

const treatments = [
    {
        title: "Cosmetic Dentistry",
        description: "Transform your smile with veneers, whitening, and bonding. We design smiles that look natural and radiant.",
        icon: Sparkles,
        href: "/treatments/cosmetic",
        color: "text-primary",
        bg: "bg-primary/10",
    },
    {
        title: "Orthodontics",
        description: "Straighten your teeth with modern braces or clear aligners like Invisalign. Perfect for all ages.",
        icon: Smile,
        href: "/treatments/orthodontics",
        color: "text-primary",
        bg: "bg-primary/10",
    },
    {
        title: "Dental Implants",
        description: "Restore missing teeth with permanent, natural-looking implants. The gold standard for tooth replacement.",
        icon: Hammer,
        href: "/treatments/implants",
        color: "text-primary",
        bg: "bg-primary/10",
    },
    {
        title: "General Checkups",
        description: "Preventive care to keep your teeth and gums healthy. Regular cleanings, exams, and x-rays.",
        icon: Stethoscope,
        href: "/treatments/general",
        color: "text-primary",
        bg: "bg-primary/10",
    },
    {
        title: "Pediatric Dentistry",
        description: "Gentle care for your little ones. We make visiting the dentist fun and educational for children.",
        icon: Smile,
        href: "/treatments/pediatric",
        color: "text-primary",
        bg: "bg-primary/10",
    },
    {
        title: "Emergency Care",
        description: "Immediate attention for toothaches, broken teeth, and other dental emergencies. We are here when you need us.",
        icon: HeartPulse,
        href: "/treatments/emergency",
        color: "text-primary",
        bg: "bg-primary/10",
    },
]

export default function TokenTreatmentsPage() {
    const { demoLink } = useDemo()

    return (
        <main className="flex min-h-screen flex-col pt-24 pb-20 bg-background relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-[500px] bg-gradient-to-b from-primary/5 to-transparent pointer-events-none" />

            <div className="container px-8 sm:px-4 md:px-12 space-y-16 relative z-10">
                <div className="text-center max-w-3xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <div className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium text-muted-foreground bg-muted/50 backdrop-blur-sm">
                        World-Class Care
                    </div>
                    <h1 className="text-4xl md:text-7xl font-bold tracking-tighter bg-clip-text text-transparent bg-gradient-to-b from-foreground to-foreground/70">
                        Our Treatments
                    </h1>
                    <p className="text-xl text-muted-foreground leading-relaxed">
                        Comprehensive dental care tailored to your unique needs. <br className="hidden md:block" />
                        From routine checkups to complex makeovers, we have you covered.
                    </p>
                </div>

                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {treatments.map((treatment) => (
                        <Link
                            key={treatment.title}
                            href={demoLink(treatment.href)}
                            className="group relative overflow-hidden rounded-[2rem] border bg-card/50 backdrop-blur-sm p-8 transition-all duration-300 hover:shadow-2xl hover:-translate-y-1 hover:border-primary/20"
                        >
                            <div className="absolute inset-0 bg-gradient-to-br from-transparent via-transparent to-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                            <div className={`mb-6 inline-flex h-16 w-16 items-center justify-center rounded-2xl ${treatment.bg} ${treatment.color} transition-transform group-hover:scale-110 duration-300`}>
                                <treatment.icon className="h-8 w-8" />
                            </div>

                            <h3 className="mb-3 text-2xl font-bold tracking-tight group-hover:text-primary transition-colors">
                                {treatment.title}
                            </h3>
                            <p className="mb-8 text-muted-foreground leading-relaxed">
                                {treatment.description}
                            </p>

                            <div className="absolute bottom-8 left-8 right-8 flex items-center justify-between border-t pt-4 border-border/50">
                                <span className="text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">Learn more</span>
                                <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center group-hover:bg-primary group-hover:text-primary-foreground transition-all">
                                    <ArrowRight className="h-4 w-4" />
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            </div>

            {/* Final CTA */}
            <CTABanner />
        </main>
    )
}
