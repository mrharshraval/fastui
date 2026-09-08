"use client"

import useEmblaCarousel from 'embla-carousel-react'

export function PublicCarouselSection({ data }) {
    const [emblaRef] = useEmblaCarousel({ loop: true })
    const images = data?.images || []

    if (images.length === 0) return null

    return (
        <div className="relative mb-12 py-4">
            <div className="overflow-hidden cursor-grab active:cursor-grabbing" ref={emblaRef}>
                <div className="flex gap-4">
                    {images.map((src, index) => (
                        <div className="flex-[0_0_80%] md:flex-[0_0_50%] min-w-0 relative aspect-video" key={index}>
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                                src={src}
                                alt={`Slide ${index + 1}`}
                                className="block h-full w-full object-cover rounded-xl"
                            />
                        </div>
                    ))}
                </div>
            </div>
            <p className="text-center text-sm text-muted-foreground mt-4">Swipe to view more photos</p>
        </div>
    )
}
