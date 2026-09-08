"use client"

import Image from "next/image"
import { CheckCircle2 } from "lucide-react"
import { EditableText } from "@/components/admin/builder/editable-text"

const alignmentClasses = {
    left: "text-left",
    center: "text-center",
    right: "text-right",
}

export function TwoColumnSection({ data, onDataChange, isEditable = false, layerState = {} }) {
    if (!data) return null

    const isImageRight = data.imagePosition === "right"
    const align = alignmentClasses[data.alignment] || alignmentClasses.left

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
            className={`py-20 bg-background ${getLayerStyle("container")}`}
            data-layer-id={isEditable ? "container" : undefined}
            data-layer-type={isEditable ? "section" : undefined}
        >
            <div className="container px-8 sm:px-4 md:px-12">
                <div className={`grid gap-12 lg:grid-cols-2 items-center ${isImageRight ? '' : 'lg:grid-flow-col-dense'}`}>
                    <div
                        className={`space-y-6 ${isImageRight ? '' : 'lg:col-start-2'} ${align} ${getLayerStyle("content-col")}`}
                        data-layer-id={isEditable ? "content-col" : undefined}
                        data-layer-type={isEditable ? "container" : undefined}
                    >
                        {(data.title || isEditable) && (
                            <h2
                                className={`text-3xl font-bold tracking-tighter sm:text-4xl ${getLayerStyle("title")}`}
                                data-layer-id={isEditable ? "title" : undefined}
                                data-layer-type={isEditable ? "text" : undefined}
                            >
                                {isEditable ? (
                                    <EditableText
                                        value={data.title}
                                        onChange={(v) => handleChange("title", v)}
                                        placeholder="Add title..."
                                        className="text-3xl font-bold tracking-tighter sm:text-4xl"
                                    />
                                ) : data.title}
                            </h2>
                        )}
                        {(data.content || isEditable) && (
                            <p
                                className={`text-muted-foreground text-lg leading-relaxed ${getLayerStyle("content")}`}
                                data-layer-id={isEditable ? "content" : undefined}
                                data-layer-type={isEditable ? "text" : undefined}
                            >
                                {isEditable ? (
                                    <EditableText
                                        value={data.content}
                                        onChange={(v) => handleChange("content", v)}
                                        placeholder="Add content..."
                                        className="text-muted-foreground text-lg leading-relaxed"
                                        multiline
                                    />
                                ) : data.content}
                            </p>
                        )}
                        {data.bullets?.length > 0 && (
                            <div
                                className={`grid gap-4 sm:grid-cols-2 mt-8 ${getLayerStyle("bullets")}`}
                                data-layer-id={isEditable ? "bullets" : undefined}
                                data-layer-type={isEditable ? "list" : undefined}
                            >
                                {data.bullets.map((item, i) => (
                                    <div key={i} className="flex items-center gap-2">
                                        <CheckCircle2 className="h-5 w-5 text-primary" />
                                        <span className="font-medium">{item}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                    <div
                        className={`relative aspect-square lg:aspect-[4/3] rounded-2xl overflow-hidden ${isImageRight ? '' : 'lg:col-start-1'} ${getLayerStyle("image-col")}`}
                        data-layer-id={isEditable ? "image-col" : undefined}
                        data-layer-type={isEditable ? "container" : undefined}
                    >
                        {data.image ? (
                            <div
                                className={`w-full h-full ${getLayerStyle("image")}`}
                                data-layer-id={isEditable ? "image" : undefined}
                                data-layer-type={isEditable ? "image" : undefined}
                            >
                                <Image
                                    src={data.image}
                                    alt={data.title || "Image"}
                                    fill
                                    className="object-cover"
                                />
                            </div>
                        ) : (
                            <div className="absolute inset-0 bg-muted flex items-center justify-center text-muted-foreground">
                                Image Placeholder
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </section>
    )
}
