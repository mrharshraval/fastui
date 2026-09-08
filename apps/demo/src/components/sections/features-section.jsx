"use client"

import { CheckCircle2 } from "lucide-react"

export function FeaturesSection({ data, onDataChange, isEditable = false, layerState = {} }) {
    if (!data?.features?.length) return null

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
                {(data.title || data.description) && (
                    <div
                        className={`mb-16 space-y-4 ${getLayerStyle("header")}`}
                        data-layer-id={isEditable ? "header" : undefined}
                        data-layer-type={isEditable ? "container" : undefined}
                    >
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
                                className={`text-muted-foreground text-lg max-w-2xl ${getLayerStyle("description")}`}
                                data-layer-id={isEditable ? "description" : undefined}
                                data-layer-type={isEditable ? "text" : undefined}
                            >
                                {data.description}
                            </p>
                        )}
                    </div>
                )}
                <div
                    className={`grid gap-8 md:grid-cols-3 ${getLayerStyle("grid")}`}
                    data-layer-id={isEditable ? "grid" : undefined}
                    data-layer-type={isEditable ? "grid" : undefined}
                >
                    {data.features.map((feature, i) => (
                        <div
                            key={i}
                            className={`bg-background p-8 rounded-xl ${getLayerStyle(`feature-${i}`)}`}
                            data-layer-id={isEditable ? `feature-${i}` : undefined}
                            data-layer-type={isEditable ? "card" : undefined}
                        >
                            <div className="h-12 w-12 rounded-lg bg-background flex items-center justify-center text-foreground mb-6">
                                <CheckCircle2 className="h-6 w-6" />
                            </div>
                            <h3 className="font-bold text-xl mb-3 text-foreground">{feature.title}</h3>
                            <p className="text-muted-foreground leading-relaxed">{feature.description}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    )
}
