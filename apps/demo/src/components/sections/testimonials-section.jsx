"use client"

import { Star, Quote } from "lucide-react"

export function TestimonialsSection({ data, onDataChange, isEditable = false, layerState = {} }) {
    if (!data?.testimonials?.length) return null

    // Helper to get layer-specific styles (visibility/locking)
    const getLayerStyle = (elementId) => {
        const state = layerState[elementId] || {}
        if (state.hidden) {
            return isEditable ? "opacity-50 grayscale" : "hidden"
        }
        if (state.locked && isEditable) {
            return "pointer-events-none"
        }
        return ""
    }

    return (
        <section
            className={`w-full py-24 bg-muted md:bg-muted/30 ${getLayerStyle("container")}`}
            data-layer-id={isEditable ? "container" : undefined}
            data-layer-type={isEditable ? "section" : undefined}
        >
            <div className="container px-8 sm:px-4 md:px-12">
                {data.title && (
                    <h2
                        className={`text-3xl font-bold tracking-tighter sm:text-4xl mb-16 ${getLayerStyle("title")}`}
                        data-layer-id={isEditable ? "title" : undefined}
                        data-layer-type={isEditable ? "text" : undefined}
                    >
                        {data.title}
                    </h2>
                )}
                <div
                    className={`grid gap-8 md:grid-cols-2 lg:grid-cols-3 ${getLayerStyle("grid")}`}
                    data-layer-id={isEditable ? "grid" : undefined}
                    data-layer-type={isEditable ? "grid" : undefined}
                >
                    {data.testimonials.map((testimonial, i) => (
                        <div
                            key={i}
                            className={`bg-background p-8 rounded-xl relative ${getLayerStyle(`testimonial-${i}`)}`}
                            data-layer-id={isEditable ? `testimonial-${i}` : undefined}
                            data-layer-type={isEditable ? "card" : undefined}
                        >
                            <Quote className="absolute top-8 right-8 h-8 w-8 text-muted-foreground/20" />
                            <div className="flex gap-1 mb-4">
                                {[1, 2, 3, 4, 5].map((star) => (
                                    <Star key={star} className="h-4 w-4 fill-foreground text-foreground" />
                                ))}
                            </div>
                            <p className="text-muted-foreground leading-relaxed mb-6">"{testimonial.text}"</p>
                            <p className="font-bold text-foreground">{testimonial.name}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    )
}
