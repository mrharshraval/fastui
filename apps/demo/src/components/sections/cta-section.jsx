"use client"

import { Button } from "@/components/ui/button"
import Link from "next/link"
import { EditableText } from "@/components/admin/builder/editable-text"

const alignmentClasses = {
    left: { text: "text-left", items: "items-start" },
    center: { text: "text-center", items: "items-center" },
    right: { text: "text-right", items: "items-end" },
}

export function CTASection({ data, onDataChange, isEditable = false, layerState = {} }) {
    if (!data?.title && !isEditable) return null

    const align = alignmentClasses[data?.alignment] || alignmentClasses.center

    const handleChange = (field, value) => {
        if (onDataChange) {
            onDataChange({ ...data, [field]: value })
        }
    }

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
            className={`w-full py-24 bg-primary text-primary-foreground relative overflow-hidden ${getLayerStyle("container")}`}
            data-layer-id={isEditable ? "container" : undefined}
            data-layer-type={isEditable ? "section" : undefined}
        >
            <div className="absolute inset-0 bg-primary-foreground/5" />
            <div className={`container px-8 sm:px-4 md:px-12 relative z-10 space-y-8 flex flex-col ${align.items} ${align.text}`}>
                <h2
                    className={`text-4xl md:text-6xl font-bold tracking-tighter max-w-3xl ${getLayerStyle("title")}`}
                    data-layer-id={isEditable ? "title" : undefined}
                    data-layer-type={isEditable ? "text" : undefined}
                >
                    {isEditable ? (
                        <EditableText
                            value={data?.title}
                            onChange={(v) => handleChange("title", v)}
                            placeholder="Add CTA title..."
                            className="text-4xl md:text-6xl font-bold tracking-tighter"
                        />
                    ) : data?.title}
                </h2>
                {(data?.description || isEditable) && (
                    <p
                        className={`text-xl max-w-2xl opacity-90 ${getLayerStyle("description")}`}
                        data-layer-id={isEditable ? "description" : undefined}
                        data-layer-type={isEditable ? "text" : undefined}
                    >
                        {isEditable ? (
                            <EditableText
                                value={data?.description}
                                onChange={(v) => handleChange("description", v)}
                                placeholder="Add description..."
                                className="text-xl opacity-90"
                                multiline
                            />
                        ) : data?.description}
                    </p>
                )}
                {(data?.buttonText || isEditable) && (
                    <div
                        className={getLayerStyle("button-wrapper")}
                        data-layer-id={isEditable ? "button-wrapper" : undefined}
                        data-layer-type={isEditable ? "container" : undefined}
                    >
                        {isEditable ? (
                            <Button
                                size="lg"
                                variant="secondary"
                                className={`rounded-full h-14 px-10 text-lg font-bold hover:scale-105 transition-transform bg-background text-foreground hover:bg-muted ${getLayerStyle("button")}`}
                                data-layer-id={isEditable ? "button" : undefined}
                                data-layer-type={isEditable ? "button" : undefined}
                            >
                                <EditableText
                                    value={data?.buttonText}
                                    onChange={(v) => handleChange("buttonText", v)}
                                    placeholder="Button text..."
                                    className="text-lg font-bold"
                                />
                            </Button>
                        ) : (
                            <Button size="lg" variant="secondary" className="rounded-full h-14 px-10 text-lg font-bold hover:scale-105 transition-transform bg-background text-foreground hover:bg-muted" asChild>
                                <Link href={data?.buttonLink || "#"}>{data?.buttonText}</Link>
                            </Button>
                        )}
                    </div>
                )}
            </div>
        </section>
    )
}
