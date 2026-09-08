"use client"

import * as React from "react"
import useEmblaCarousel from "embla-carousel-react"
import { ArrowLeft, ArrowRight, Star, ImageIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const MIN_ITEMS = 2

export function SmileGallerySection({ data }) {
    const [emblaRef, emblaApi] = useEmblaCarousel({ loop: true, align: "start" })
    const [selectedIndex, setSelectedIndex] = React.useState(0)
    const [scrollSnaps, setScrollSnaps] = React.useState([])

    const items = data?.items || []

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

    // Show placeholder if not enough items
    if (items.length < MIN_ITEMS) {
        return (
            <section className="w-full py-24 bg-background overflow-hidden">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="flex flex-col items-center text-center mb-12 space-y-4 max-w-2xl mx-auto">
                        <div className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium text-muted-foreground bg-muted/50">
                            <Star className="mr-2 h-3.5 w-3.5 fill-primary text-primary" />
                            {data?.badge || "Gallery"}
                        </div>
                        <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">
                            {data?.title || "Before & After Gallery"}
                        </h2>
                        {data?.description && (
                            <p className="text-muted-foreground text-lg">{data.description}</p>
                        )}
                    </div>
                    <div className="p-12 border-2 border-dashed border-muted-foreground/30 rounded-xl text-center">
                        <ImageIcon className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
                        <p className="text-muted-foreground">Add at least {MIN_ITEMS} items to enable the carousel</p>
                        <p className="text-sm text-muted-foreground/60 mt-1">Currently: {items.length} items</p>
                    </div>
                </div>
            </section>
        )
    }

    return (
        <section className="w-full py-24 bg-background overflow-hidden">
            <div className="container px-8 sm:px-4 md:px-12">
                <div className="flex flex-col items-center text-center mb-12 space-y-4 max-w-2xl mx-auto">
                    <div className="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium text-muted-foreground bg-muted/50">
                        <Star className="mr-2 h-3.5 w-3.5 fill-primary text-primary" />
                        {data?.badge || "Real Results"}
                    </div>
                    <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">
                        {data?.title || "Real Results, Real Smiles"}
                    </h2>
                    {data?.description && (
                        <p className="text-muted-foreground text-lg">{data.description}</p>
                    )}
                </div>

                <div className="overflow-hidden" ref={emblaRef}>
                    <div className="flex -ml-4">
                        {items.map((item, index) => (
                            <div key={item.id || index} className="flex-[0_0_100%] min-w-0 pl-4 md:flex-[0_0_50%] lg:flex-[0_0_33.33%]">
                                <div className="group relative rounded-3xl overflow-hidden border bg-card h-full flex flex-col">
                                    <div className="aspect-[4/3] relative shrink-0">
                                        <div className="absolute inset-0 flex">
                                            <div className="w-1/2 h-full bg-muted relative border-r border-white/20">
                                                <div className="absolute top-3 left-3 bg-black/50 text-white text-[10px] font-bold px-2 py-1 rounded-full backdrop-blur-sm z-10">BEFORE</div>
                                                {item.before ? (
                                                    <img src={item.before} alt="Before" className="w-full h-full object-cover" />
                                                ) : (
                                                    <div className="w-full h-full bg-neutral-200 flex items-center justify-center text-neutral-400 text-xs">Before</div>
                                                )}
                                            </div>
                                            <div className="w-1/2 h-full bg-muted relative">
                                                <div className="absolute top-3 right-3 bg-primary text-primary-foreground text-[10px] font-bold px-2 py-1 rounded-full shadow-sm z-10">AFTER</div>
                                                {item.after ? (
                                                    <img src={item.after} alt="After" className="w-full h-full object-cover" />
                                                ) : (
                                                    <div className="w-full h-full bg-neutral-100 flex items-center justify-center text-neutral-400 text-xs">After</div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="p-6 space-y-2 flex-grow">
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
                                        ? "border-foreground bg-foreground"
                                        : "border-muted-foreground/30 hover:border-muted-foreground/50"
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
                        >
                            <ArrowLeft className="h-5 w-5" />
                            <span className="sr-only">Previous</span>
                        </Button>

                        <Button
                            variant="outline"
                            size="icon"
                            className="rounded-full h-12 w-12 border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-all duration-300"
                            onClick={scrollNext}
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
