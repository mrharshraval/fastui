"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { useDemo } from "@/lib/demo-context"
import { CTABanner } from "@/components/sections/cta-banner"

export default function TokenSmileGallery() {
    const { demoLink } = useDemo()

    const cases = [
        { title: "Gap Teeth Correction", type: "Cosmetic Bonding", desc: "Comprehensive alignment and aesthetic bonding for a seamless, confident smile.", image: "/before-after/gap-teeth.png" },
        { title: "Chipped Tooth Restoration", type: "Restorative Bonding", desc: "Composite bonding restores natural tooth shape, contour, and aesthetic symmetry.", image: "/before-after/chipped-tooth.png" },
        { title: "Crooked Teeth Alignment", type: "Clear Aligners", desc: "Gentle teeth alignment without traditional metal braces.", image: "/before-after/crooked-teeth.png" },
        { title: "Missing Tooth Replacement", type: "Dental Implant", desc: "Seamless, permanent replacement of a missing tooth with natural look and feel.", image: "/before-after/missing-tooth.png" },
        { title: "In-Office Teeth Whitening", type: "Laser Whitening", desc: "Brightening a smile by multiple shades in a single clinical visit.", image: "/before-after/discolored-teeth.png" },
        { title: "Aesthetic Gum Contouring", type: "Laser Contouring", desc: "Reshaping the gum line for a harmonious, confident, balanced smile.", image: "/before-after/uneven-gums.png" }
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
                                <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl bg-muted border border-border">
                                    <img
                                        src={item.image}
                                        alt={item.title}
                                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                                        loading="lazy"
                                    />
                                    <div className="absolute top-3 left-3 bg-white/90 text-neutral-900 border border-black/10 text-[10px] font-bold px-2.5 py-1 rounded-full backdrop-blur-sm z-10 shadow-sm">
                                        BEFORE
                                    </div>
                                    <div className="absolute top-3 right-3 bg-primary text-primary-foreground text-[10px] font-bold px-2.5 py-1 rounded-full shadow-sm z-10">
                                        AFTER
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
