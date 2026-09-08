"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { useDemo } from "@/lib/demo-context"
import { CTABanner } from "@/components/sections/cta-banner"

export default function TokenSmileGallery() {
    const { demoLink } = useDemo()

    const cases = [
        { title: "Full Mouth Reconstruction", type: "Implants & Veneers", desc: "Complete restoration of function and aesthetics." },
        { title: "Smile Makeover", type: "Porcelain Veneers", desc: "Correcting discoloration, chips, and spacing issues." },
        { title: "Clear Aligner Transformation", type: "Orthodontics", desc: "Gentle teeth alignment without traditional metal braces." },
        { title: "Single Tooth Replacement", type: "Dental Implant", desc: "Seamless, permanent replacement of a missing front tooth." },
        { title: "In-Office Teeth Whitening", type: "Laser Whitening", desc: "Brightening a smile by multiple shades in a single visit." },
        { title: "Aesthetic Gum Contouring", type: "Laser Contouring", desc: "Reshaping the gum line for a harmonious, confident smile." }
    ]

    return (
        <main className="flex flex-col min-h-screen bg-background">
            {/* Hero Section */}
            <section className="w-full py-24 bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="flex flex-col items-center text-center md:items-start md:text-left gap-6 max-w-3xl mx-auto md:mx-0">
                        <div className="inline-flex items-center rounded-full border bg-background px-3 py-1 text-sm font-medium text-muted-foreground border-border w-fit">
                            Smile Gallery
                        </div>
                        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none text-foreground text-center md:text-left">
                            Real patients. Real results.
                        </h1>
                        <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl text-center md:text-left">
                            Browse our clinical smile gallery to see the transformative power of modern dental treatments.
                        </p>
                    </div>
                </div>
            </section>

            {/* Gallery Grid */}
            <section className="w-full py-16 bg-background">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="grid gap-12 md:grid-cols-2 lg:grid-cols-3">
                        {cases.map((item, index) => (
                            <div key={index} className="flex flex-col items-center text-center md:items-start md:text-left space-y-4 group">
                                <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl bg-muted/50 border border-border">
                                    <div className="absolute inset-0 flex items-center justify-center text-muted-foreground font-medium">
                                        Clinical Case Photo
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <div className="text-sm font-medium text-primary">{item.type}</div>
                                    <h3 className="text-xl font-bold group-hover:text-primary transition-colors">{item.title}</h3>
                                    <p className="text-muted-foreground text-sm leading-relaxed">{item.desc}</p>
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
