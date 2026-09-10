"use client"

import Image from "next/image"
import { Button } from "@/components/ui/button"
import { CheckCircle2 } from "lucide-react"
import Link from "next/link"
import { EditableText } from "@/components/admin/builder/editable-text"

const alignmentClasses = {
    left: { text: "text-left", items: "items-start", justify: "justify-start" },
    center: { text: "text-center", items: "items-center", justify: "justify-center" },
    right: { text: "text-right", items: "items-end", justify: "justify-end" },
}

export function HeroSection({ data, onDataChange, isEditable = false, layerState = {} }) {
    if (!data) return null

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

    // Wrapper for editable or static text
    const Text = ({ field, value, children, className = "", multiline = false }) => {
        if (isEditable) {
            return (
                <EditableText
                    value={value}
                    onChange={(v) => handleChange(field, v)}
                    className={className}
                    multiline={multiline}
                    placeholder={`Add ${field}...`}
                />
            )
        }
        return children
    }

    return (
        <div className="w-full">
            {/* Desktop Hero - 21:9 */}
            <div
                className={`hidden md:block relative w-full aspect-[21/9] overflow-hidden ${getLayerStyle("container")}`}
                data-layer-id={isEditable ? "container" : undefined}
                data-layer-type={isEditable ? "container" : undefined}
            >
                {data.image && (
                    <Image
                        src={data.image}
                        alt={data.title || "Hero"}
                        fill
                        className={`object-cover object-center ${getLayerStyle("main-image")}`}
                        priority
                        sizes="100vw"
                        data-layer-id={isEditable ? "main-image" : undefined}
                        data-layer-type={isEditable ? "image" : undefined}
                    />
                )}
                <div
                    className="absolute inset-0 bg-foreground/5"
                // Overlay is internal layout, clicks bubble to container
                >
                    <div
                        className={`absolute inset-0 z-20 flex flex-col justify-between p-12 md:p-24 ${align.items} ${getLayerStyle("content-overlay")}`}
                        data-layer-id={isEditable ? "content-overlay" : undefined}
                        data-layer-type={isEditable ? "container" : undefined}
                    >
                        <div className={`mt-24 max-w-4xl ${align.text}`}>
                            {(data.title || isEditable) && (
                                <h1
                                    className={`text-5xl md:text-7xl font-bold tracking-tight text-foreground mb-6 ${getLayerStyle("title")}`}
                                    data-layer-id={isEditable ? "title" : undefined}
                                    data-layer-type={isEditable ? "text" : undefined}
                                >
                                    <Text field="title" value={data.title} multiline>
                                        {data.title}
                                    </Text>
                                </h1>
                            )}
                            {(data.subtitle || isEditable) && (
                                <p
                                    className={`text-xl md:text-2xl text-muted-foreground mb-12 max-w-2xl leading-relaxed ${getLayerStyle("subtitle")}`}
                                    data-layer-id={isEditable ? "subtitle" : undefined}
                                    data-layer-type={isEditable ? "text" : undefined}
                                >
                                    <Text field="subtitle" value={data.subtitle} multiline>
                                        {data.subtitle}
                                    </Text>
                                </p>
                            )}
                            {(data.buttonText || isEditable) && (
                                <div
                                    className={`flex ${align.justify} ${getLayerStyle("cta-group")}`}
                                    data-layer-id={isEditable ? "cta-group" : undefined}
                                    data-layer-type={isEditable ? "container" : undefined}
                                >
                                    {isEditable ? (
                                        <div
                                            data-layer-id="primary-btn"
                                            data-layer-type="button"
                                            className={getLayerStyle("primary-btn")}
                                        >
                                            <Button className="rounded-full h-14 px-8 text-lg font-medium transition-all hover:scale-105">
                                                <Text field="buttonText" value={data.buttonText} className="text-lg font-medium">
                                                    {data.buttonText || "Button Text"}
                                                </Text>
                                            </Button>
                                        </div>
                                    ) : (
                                        <Button className="rounded-full h-14 px-8 text-lg font-medium transition-all hover:scale-105" asChild>
                                            <Link href={data.buttonLink || "#"}>{data.buttonText}</Link>
                                        </Button>
                                    )}
                                </div>
                            )}
                        </div>
                        {data.badges?.length > 0 && (
                            <div
                                className={`flex flex-col sm:flex-row gap-8 mt-auto ${align.justify}`}
                                data-layer-id={isEditable ? "badges" : undefined}
                                data-layer-type={isEditable ? "group" : undefined}
                            >
                                {data.badges.map((badge, i) => (
                                    <div key={i} className="flex items-center gap-2">
                                        <div className="h-6 w-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
                                            <CheckCircle2 className="h-4 w-4" />
                                        </div>
                                        <span className="font-medium text-foreground">{badge}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Mobile Hero - Stacked */}
            <div
                className="block md:hidden w-full px-4 pb-8"
                data-layer-id={isEditable ? "container" : undefined}
                data-layer-type={isEditable ? "container" : undefined}
            >
                {data.image && (
                    <div
                        className="relative w-full aspect-[4/3] rounded-2xl overflow-hidden mb-8"
                        data-layer-id={isEditable ? "image-wrapper" : undefined}
                        data-layer-type={isEditable ? "container" : undefined}
                    >
                        <Image
                            src={data.image}
                            alt={data.title || "Hero"}
                            fill
                            className="object-cover object-center"
                            priority
                            sizes="100vw"
                            data-layer-id={isEditable ? "main-image" : undefined}
                            data-layer-type={isEditable ? "image" : undefined}
                        />
                    </div>
                )}
                <div
                    className={`flex flex-col ${align.items} ${align.text} space-y-6`}
                    data-layer-id={isEditable ? "content" : undefined}
                    data-layer-type={isEditable ? "container" : undefined}
                >
                    {(data.badges?.length > 0) && (
                        <div
                            className="flex flex-wrap gap-4 justify-center"
                            data-layer-id={isEditable ? "badges" : undefined}
                            data-layer-type={isEditable ? "group" : undefined}
                        >
                            {data.badges.map((badge, i) => (
                                <div key={i} className="flex items-center gap-2">
                                    <div className="h-5 w-5 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
                                        <CheckCircle2 className="h-3 w-3" />
                                    </div>
                                    <span className="font-medium text-foreground text-sm">{badge}</span>
                                </div>
                            ))}
                        </div>
                    )}
                    {(data.title || isEditable) && (
                        <h1
                            className="text-5xl font-regular tracking-tight text-foreground leading-[1.1]"
                            data-layer-id={isEditable ? "title" : undefined}
                            data-layer-type={isEditable ? "text" : undefined}
                        >
                            <Text field="title" value={data.title} className="text-5xl font-regular tracking-tight text-foreground leading-[1.1]">
                                {data.title}
                            </Text>
                        </h1>
                    )}
                    {(data.subtitle || isEditable) && (
                        <p
                            className="text-xl font-regular tracking-tight text-muted-foreground leading-[1.2]"
                            data-layer-id={isEditable ? "subtitle" : undefined}
                            data-layer-type={isEditable ? "text" : undefined}
                        >
                            <Text field="subtitle" value={data.subtitle} className="text-xl font-regular tracking-tight text-muted-foreground leading-[1.2]" multiline>
                                {data.subtitle}
                            </Text>
                        </p>
                    )}
                    {(data.buttonText || isEditable) && (
                        <div
                            className="w-full pt-4"
                            data-layer-id={isEditable ? "cta-group" : undefined}
                            data-layer-type={isEditable ? "container" : undefined}
                        >
                            {isEditable ? (
                                <div data-layer-id="primary-btn" data-layer-type="button">
                                    <Button className="w-full rounded-full h-14 text-lg font-medium">
                                        <Text field="buttonText" value={data.buttonText} className="text-lg font-medium">
                                            {data.buttonText || "Button Text"}
                                        </Text>
                                    </Button>
                                </div>
                            ) : (
                                <Button className="w-full rounded-full h-14 text-lg font-medium" asChild>
                                    <Link href={data.buttonLink || "#"}>{data.buttonText}</Link>
                                </Button>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
