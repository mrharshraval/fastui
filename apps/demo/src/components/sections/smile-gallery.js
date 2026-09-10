"use client"

import * as React from "react"
import useEmblaCarousel from "embla-carousel-react"
import { ArrowLeft, ArrowRight, Star } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import Image from "next/image"

const transformations = [
    {
        id: 1,
        title: "Complete Smile Makeover",
        description: "Veneers and whitening for a radiant new look.",
        before: "/placeholder-before-1.jpg",
        after: "/placeholder-after-1.jpg",
    },
    {
        id: 2,
        title: "Invisalign Correction",
        description: "12 months of clear aligners to straighten crowding.",
        before: "/placeholder-before-2.jpg",
        after: "/placeholder-after-2.jpg",
    },
    {
        id: 3,
        title: "Dental Implants",
        description: "Restoring function and aesthetics with implants.",
        before: "/placeholder-before-3.jpg",
        after: "/placeholder-after-3.jpg",
    },
    {
        id: 4,
        title: "Teeth Whitening",
        description: "Professional in-office whitening for instant results.",
        before: "/placeholder-before-4.jpg",
        after: "/placeholder-after-4.jpg",
    },
]

export function SmileGallery() {
    const [emblaRef, emblaApi] = useEmblaCarousel({ loop: true, align: "start" })
    const [selectedIndex, setSelectedIndex] = React.useState(0)
    const [scrollSnaps, setScrollSnaps] = React.useState([])

    const scrollPrev = React.useCallback(() => {
        if (emblaApi) emblaApi.scrollPrev()
    }, [emblaApi])

    const scrollNext = React.useCallback(() => {
        if (emblaApi) emblaApi.scrollNext()
    }, [emblaApi])

    const scrollTo = React.useCallback(
        (index) => {
            if (emblaApi) emblaApi.scrollTo(index)
        },
        [emblaApi]
    )

    const onInit = React.useCallback((emblaApi) => {
        setScrollSnaps(emblaApi.scrollSnapList())
    }, [])

    const onSelect = React.useCallback((emblaApi) => {
        setSelectedIndex(emblaApi.selectedScrollSnap())
    }, [])

    React.useEffect(() => {
        if (!emblaApi) return

        onInit(emblaApi)
        onSelect(emblaApi)
        emblaApi.on("reInit", onInit)
        emblaApi.on("reInit", onSelect)
        emblaApi.on("select", onSelect)
    }, [emblaApi, onInit, onSelect])

    return (
        <section className="w-full py-24 bg-background overflow-hidden">
            <div className="container px-8 sm:px-4 md:px-12">
                <div className="flex flex-col items-center text-center mb-12 space-y-4 max-w-2xl mx-auto">
                    <div className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium text-muted-foreground bg-muted/50">
                        <Star className="mr-2 h-3.5 w-3.5 fill-primary text-primary" />
                        Real Results
                    </div>
                    <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">
                        Real Results, Real Smiles
                    </h2>
                    <p className="text-muted-foreground text-lg">
                        See the life-changing transformations we've achieved for our patients.
                    </p>
                </div>

                <div className="overflow-hidden" ref={emblaRef}>
                    <div className="flex -ml-4">
                        {transformations.map((item) => (
                            <div key={item.id} className="flex-[0_0_100%] min-w-0 pl-4 md:flex-[0_0_50%] lg:flex-[0_0_33.33%]">
                                <div className="group relative rounded-3xl overflow-hidden border bg-card h-full flex flex-col">
                                    <div className="aspect-[4/3] relative shrink-0">
                                        <div className="absolute inset-0 flex">
                                            <div className="w-1/2 h-full bg-muted relative border-r border-border">
                                                <div className="absolute top-3 left-3 bg-background/70 text-foreground border border-border/40 text-[10px] font-bold px-2 py-1 rounded-full backdrop-blur-sm z-10">BEFORE</div>
                                                <div className="w-full h-full bg-muted flex items-center justify-center text-muted-foreground text-xs">Image</div>
                                            </div>
                                            <div className="w-1/2 h-full bg-muted relative">
                                                <div className="absolute top-3 right-3 bg-primary text-primary-foreground text-[10px] font-bold px-2 py-1 rounded-full shadow-sm z-10">AFTER</div>
                                                <div className="w-full h-full bg-muted/60 flex items-center justify-center text-muted-foreground text-xs">Image</div>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="p-6 space-y-2 flex-grow text-center md:text-left">
                                        <h3 className="font-bold text-xl">{item.title}</h3>
                                        <p className="text-muted-foreground text-sm">{item.description}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Navigation Controls */}
                <div className="flex items-center justify-between mt-10">
                    <div className="flex gap-2">
                        {scrollSnaps.map((_, index) => (
                            <button
                                key={index}
                                className={cn(
                                    "h-3 w-3 rounded-full border transition-all duration-300",
                                    index === selectedIndex
                                        ? "border-foreground bg-foreground" // Active
                                        : "border-muted-foreground/30 hover:border-muted-foreground/50" // Inactive
                                )}
                                onClick={() => scrollTo(index)}
                                aria-label={`Go to slide ${index + 1}`}
                            />
                        ))}
                    </div>

                    <div className="flex items-center gap-4">
                        <Button
                            variant="outline"
                            size="icon"
                            className="rounded-full h-12 w-12 border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-all duration-300"
                            onClick={scrollPrev}
                            disabled={!emblaApi?.canScrollPrev()}
                        >
                            <ArrowLeft className="h-5 w-5" />
                            <span className="sr-only">Previous</span>
                        </Button>

                        <Button
                            variant="outline"
                            size="icon"
                            className="rounded-full h-12 w-12 border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-all duration-300"
                            onClick={scrollNext}
                            disabled={!emblaApi?.canScrollNext()}
                        >
                            <ArrowRight className="h-5 w-5" />
                            <span className="sr-only">Next</span>
                        </Button>
                    </div>
                </div>
            </div>
        </section>
    )
}
