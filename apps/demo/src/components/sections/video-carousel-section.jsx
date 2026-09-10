"use client"

import * as React from "react"
import { Play, Pause, ArrowLeft, ArrowRight, Film } from "lucide-react"
import { cn } from "@/lib/utils"

import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
    Carousel,
    CarouselContent,
    CarouselItem,
} from "@/components/ui/carousel"

const MIN_ITEMS = 2

function TestimonialCard({ item, isPlaying, onPlay, onEnded }) {
    const videoRef = React.useRef(null)

    React.useEffect(() => {
        if (isPlaying) {
            videoRef.current?.play()
        } else {
            videoRef.current?.pause()
        }
    }, [isPlaying])

    return (
        <Card className="border-0 bg-transparent shadow-none group overflow-hidden rounded-[32px] cursor-pointer h-full">
            <CardContent className="p-0 relative aspect-[3/4] overflow-hidden bg-black rounded-[32px]">
                {item.video ? (
                    <video
                        ref={videoRef}
                        src={item.video}
                        className="w-full h-full object-cover"
                        playsInline
                        preload="metadata"
                        onClick={() => onPlay(item.id)}
                        onEnded={() => onEnded(item.id)}
                    />
                ) : (
                    <div className="w-full h-full bg-muted flex items-center justify-center text-muted-foreground">
                        <Film className="h-12 w-12" />
                    </div>
                )}

                {/* Dark Overlay - Visible when not playing */}
                <div
                    className={cn(
                        "absolute inset-0 bg-black/20 group-hover:bg-black/30 transition-colors pointer-events-none",
                        isPlaying ? "opacity-0" : "opacity-100"
                    )}
                />

                {/* Play/Pause Button Overlay */}
                <div className="absolute bottom-4 right-4 z-10 transition-opacity duration-300 opacity-100">
                    <Button
                        size="icon"
                        variant="secondary"
                        className="h-10 w-10 rounded-full bg-background/40 backdrop-blur-md text-foreground hover:bg-background/60 border border-border/40 transition-all shadow-sm"
                        onClick={(e) => {
                            e.stopPropagation()
                            onPlay(item.id)
                        }}
                    >
                        {isPlaying ? (
                            <Pause className="h-4 w-4 fill-current ml-0.5" />
                        ) : (
                            <Play className="h-4 w-4 fill-current ml-0.5" />
                        )}
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}

export function VideoCarouselSection({ data }) {
    const [api, setApi] = React.useState(null)
    const [current, setCurrent] = React.useState(0)
    const [count, setCount] = React.useState(0)
    const [playingId, setPlayingId] = React.useState(null)

    const items = data?.videos || []

    React.useEffect(() => {
        if (!api) return

        setCount(api.scrollSnapList().length)
        setCurrent(api.selectedScrollSnap() + 1)

        api.on("select", () => {
            setCurrent(api.selectedScrollSnap() + 1)
            setPlayingId(null)
        })
    }, [api])

    const handlePlay = (id) => {
        setPlayingId(playingId === id ? null : id)
    }

    const handleVideoEnded = () => {
        setPlayingId(null)
    }

    // Show placeholder if not enough items
    if (items.length < MIN_ITEMS) {
        return (
            <section className="w-full py-16 lg:py-24">
                <div className="container px-0 mx-auto">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl mb-4">
                            {data?.title || "Video Testimonials"}
                        </h2>
                        {data?.description && (
                            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">{data.description}</p>
                        )}
                    </div>
                    <div className="max-w-7xl mx-auto">
                        <div className="p-12 border-2 border-dashed border-muted-foreground/30 rounded-xl text-center">
                            <Film className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
                            <p className="text-muted-foreground">Add at least {MIN_ITEMS} videos to enable the carousel</p>
                            <p className="text-sm text-muted-foreground/60 mt-1">Currently: {items.length} videos</p>
                        </div>
                    </div>
                </div>
            </section>
        )
    }

    return (
        <section className="w-full py-16 lg:py-24">
            <div className="container px-0 mx-auto">
                <div className="text-center mb-12">
                    <h2 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl mb-4">
                        {data?.title || "Hear from our Patients"}
                    </h2>
                    {data?.description && (
                        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">{data.description}</p>
                    )}
                </div>

                <div className="relative max-w-7xl mx-auto">
                    <Carousel
                        setApi={setApi}
                        opts={{
                            align: "start",
                            loop: true,
                        }}
                        className="w-full"
                    >
                        <CarouselContent className="-ml-4 pb-4">
                            {items.map((item, index) => (
                                <CarouselItem
                                    key={item.id || index}
                                    className="pl-4 md:basis-1/2 lg:basis-1/3 xl:basis-1/4"
                                >
                                    <TestimonialCard
                                        item={{ ...item, id: item.id || index }}
                                        isPlaying={playingId === (item.id || index)}
                                        onPlay={handlePlay}
                                        onEnded={handleVideoEnded}
                                    />
                                </CarouselItem>
                            ))}
                        </CarouselContent>
                    </Carousel>

                    {/* Custom Split Navigation Controls */}
                    <div className="flex items-center justify-between mt-8">
                        {/* Left: Dots */}
                        <div className="flex gap-2">
                            {Array.from({ length: count }).map((_, index) => (
                                <button
                                    key={index}
                                    className={cn(
                                        "h-3 w-3 rounded-full border transition-all duration-300",
                                        current === index + 1
                                            ? "border-foreground bg-foreground"
                                            : "border-muted-foreground/30 hover:border-muted-foreground/50"
                                    )}
                                    onClick={() => api?.scrollTo(index)}
                                    aria-label={`Go to slide ${index + 1}`}
                                />
                            ))}
                        </div>

                        {/* Right: Buttons */}
                        <div className="flex items-center gap-4">
                            <Button
                                variant="outline"
                                size="icon"
                                className="rounded-full h-12 w-12 border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-all duration-300"
                                onClick={() => api?.scrollPrev()}
                            >
                                <ArrowLeft className="h-5 w-5" />
                                <span className="sr-only">Previous slide</span>
                            </Button>

                            <Button
                                variant="outline"
                                size="icon"
                                className="rounded-full h-12 w-12 border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-all duration-300"
                                onClick={() => api?.scrollNext()}
                            >
                                <ArrowRight className="h-5 w-5" />
                                <span className="sr-only">Next slide</span>
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    )
}
