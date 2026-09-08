"use client"

import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"

export function GallerySection({ data, onDataChange, isEditable = false, layerState = {} }) {
    if (!data?.items?.length) return null

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
            className={`w-full py-24 bg-background ${getLayerStyle("container")}`}
            data-layer-id={isEditable ? "container" : undefined}
            data-layer-type={isEditable ? "section" : undefined}
        >
            <div className="container px-8 sm:px-4 md:px-12">
                {(data.title || data.description) && (
                    <div
                        className={`flex flex-col gap-6 max-w-3xl mb-16 ${getLayerStyle("header")}`}
                        data-layer-id={isEditable ? "header" : undefined}
                        data-layer-type={isEditable ? "container" : undefined}
                    >
                        {data.badge && (
                            <div
                                className={`inline-flex items-center rounded-full border bg-background px-3 py-1 text-sm font-medium text-muted-foreground border-border w-fit ${getLayerStyle("badge")}`}
                                data-layer-id={isEditable ? "badge" : undefined}
                                data-layer-type={isEditable ? "text" : undefined}
                            >
                                {data.badge}
                            </div>
                        )}
                        {data.title && (
                            <h2
                                className={`text-3xl font-bold tracking-tighter sm:text-4xl ${getLayerStyle("title")}`}
                                data-layer-id={isEditable ? "title" : undefined}
                                data-layer-type={isEditable ? "text" : undefined}
                            >
                                {data.title}
                            </h2>
                        )}
                        {data.description && (
                            <p
                                className={`text-lg text-muted-foreground leading-relaxed max-w-2xl ${getLayerStyle("description")}`}
                                data-layer-id={isEditable ? "description" : undefined}
                                data-layer-type={isEditable ? "text" : undefined}
                            >
                                {data.description}
                            </p>
                        )}
                    </div>
                )}
                <div
                    className={`grid gap-12 md:grid-cols-2 lg:grid-cols-3 ${getLayerStyle("grid")}`}
                    data-layer-id={isEditable ? "grid" : undefined}
                    data-layer-type={isEditable ? "grid" : undefined}
                >
                    {data.items.map((item, i) => (
                        <div
                            key={i}
                            className={`group cursor-pointer ${getLayerStyle(`item-${i}`)}`}
                            data-layer-id={isEditable ? `item-${i}` : undefined}
                            data-layer-type={isEditable ? "card" : undefined}
                        >
                            <div className="relative aspect-[4/3] rounded-xl overflow-hidden bg-secondary/30 mb-6">
                                {item.image ? (
                                    <img src={item.image} alt={item.title || "Gallery item"} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                                ) : (
                                    <div className="absolute inset-0 flex items-center justify-center text-muted-foreground group-hover:scale-105 transition-transform duration-500">
                                        Before / After Image
                                    </div>
                                )}
                                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors duration-300" />
                            </div>
                            <div className="space-y-2">
                                {item.category && (
                                    <div className="text-sm font-medium text-primary">{item.category}</div>
                                )}
                                {item.title && (
                                    <h3 className="text-xl font-bold group-hover:text-primary transition-colors">{item.title}</h3>
                                )}
                                {item.description && (
                                    <p className="text-muted-foreground">{item.description}</p>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    )
}
