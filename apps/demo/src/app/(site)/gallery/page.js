"use client"

import { CTABanner } from "@/components/sections/cta-banner"

export default function SmileGallery() {
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
                            Browse our collection of before and after photos to see the transformative power of our dental treatments.
                        </p>
                    </div>
                </div>
            </section>

            {/* Gallery Grid */}
            <section className="w-full py-24 bg-background">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="grid gap-12 md:grid-cols-2 lg:grid-cols-3">
                        {[
                            { title: "Full Mouth Reconstruction", type: "Implants & Veneers", desc: "Complete restoration of function and aesthetics." },
                            { title: "Smile Makeover", type: "Porcelain Veneers", desc: "Correcting discoloration and spacing issues." },
                            { title: "Invisalign Transformation", type: "Orthodontics", desc: "Straightening crowded teeth without braces." },
                            { title: "Single Tooth Replacement", type: "Dental Implant", desc: "Seamless replacement of a missing front tooth." },
                            { title: "Teeth Whitening", type: "Zoom! Whitening", desc: "Brightening a smile by 8 shades in one visit." },
                            { title: "Gummy Smile Correction", type: "Laser Contouring", desc: "Reshaping the gum line for a balanced smile." }
                        ].map((item, i) => (
                            <div key={i} className="group cursor-pointer flex flex-col items-center text-center md:items-start md:text-left">
                                <div className="relative aspect-[4/3] rounded-xl overflow-hidden bg-secondary/30 mb-6 w-full">
                                    <div className="absolute inset-0 flex items-center justify-center text-muted-foreground group-hover:scale-105 transition-transform duration-500">
                                        Before / After Image
                                    </div>
                                    <div className="absolute inset-0 bg-foreground/0 group-hover:bg-foreground/10 transition-colors duration-300" />
                                </div>
                                <div className="space-y-2">
                                    <div className="text-sm font-medium text-primary">{item.type}</div>
                                    <h3 className="text-xl font-bold group-hover:text-primary transition-colors">{item.title}</h3>
                                    <p className="text-muted-foreground">{item.desc}</p>
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
