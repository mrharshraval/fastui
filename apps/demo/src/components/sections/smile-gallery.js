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
        title: "Gap Teeth Correction",
        description: "Comprehensive alignment and aesthetic bonding for a seamless, confident smile.",
        image: "/before-after/gap-teeth.png",
    },
    {
        id: 2,
        title: "Chipped Tooth Restoration",
        description: "Composite bonding restores natural tooth shape, contour, and aesthetic symmetry.",
        image: "/before-after/chipped-tooth.png",
    },
    {
        id: 3,
        title: "Crooked Teeth Alignment",
        description: "Clear aligner therapy gently straightens crowding and balances your bite.",
        image: "/before-after/crooked-teeth.png",
    },
    {
        id: 4,
        title: "Teeth Whitening",
        description: "Professional laser whitening removes deep discoloration for a brilliant finish.",
        image: "/before-after/discolored-teeth.png",
    },
    {
        id: 5,
        title: "Missing Tooth Replacement",
        description: "Modern dental implants restore full chewing strength and natural appearance.",
        image: "/before-after/missing-tooth.png",
    },
    {
        id: 6,
        title: "Overlapping Teeth Alignment",
        description: "Targeted orthodontics creates an even, harmonic smile line.",
        image: "/before-after/overlaping-tooth.png",
    },
    {
        id: 7,
        title: "Gum Contouring",
        description: "Gentle laser reshaping reveals a balanced, aesthetically proportionate smile.",
        image: "/before-after/uneven-gums.png",
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
                                    <div className="aspect-[4/3] relative shrink-0 overflow-hidden bg-muted">
                                        {item.image ? (
                                            <img
                                                src={item.image}
                                                alt={item.title}
                                                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                                                loading="lazy"
                                            />
                                        ) : (
                                            <div className="w-full h-full bg-muted flex items-center justify-center text-muted-foreground text-xs">
                                                Image
                                            </div>
                                        )}
                                        {/* BEFORE badge on top left */}
                                        <div className="absolute top-3 left-3 bg-white/90 text-neutral-900 border border-black/10 text-[10px] font-bold px-3 py-1 rounded-full backdrop-blur-sm z-10 shadow-sm">
                                            BEFORE
                                        </div>
                                        {/* AFTER badge on top right */}
                                        <div className="absolute top-3 right-3 bg-primary text-primary-foreground text-[10px] font-bold px-3 py-1 rounded-full shadow-sm z-10">
                                            AFTER
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
