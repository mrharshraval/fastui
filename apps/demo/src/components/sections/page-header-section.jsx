"use client"

import { EditableText } from "@/components/admin/builder/editable-text"

const alignmentClasses = {
    left: "text-left items-start",
    center: "text-center items-center",
    right: "text-right items-end",
}

export function PageHeaderSection({ data, onDataChange, isEditable = false, layerState = {} }) {
    if (!data) return null

    const align = alignmentClasses[data.alignment] || alignmentClasses.center

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
        <div
            className={`flex flex-col max-w-3xl mx-auto space-y-6 py-16 ${align} ${getLayerStyle("container")}`}
            data-layer-id={isEditable ? "container" : undefined}
            data-layer-type={isEditable ? "container" : undefined}
        >
            {(data.badge || isEditable) && (
                <div
                    className={`inline-flex items-center rounded-full bg-secondary px-3 py-1 text-sm font-medium text-secondary-foreground w-fit ${getLayerStyle("badge")}`}
                    data-layer-id={isEditable ? "badge" : undefined}
                    data-layer-type={isEditable ? "text" : undefined}
                >
                    {isEditable ? (
                        <EditableText
                            value={data.badge}
                            onChange={(v) => handleChange("badge", v)}
                            placeholder="Add badge..."
                            className="text-sm font-medium"
                        />
                    ) : data.badge}
                </div>
            )}
            {(data.title || isEditable) && (
                <h1
                    className={`text-4xl md:text-7xl font-bold tracking-tighter text-foreground ${getLayerStyle("title")}`}
                    data-layer-id={isEditable ? "title" : undefined}
                    data-layer-type={isEditable ? "text" : undefined}
                >
                    {isEditable ? (
                        <EditableText
                            value={data.title}
                            onChange={(v) => handleChange("title", v)}
                            placeholder="Add title..."
                            className="text-4xl md:text-7xl font-bold tracking-tighter"
                        />
                    ) : data.title}
                </h1>
            )}
            {(data.description || isEditable) && (
                <p
                    className={`text-xl text-muted-foreground leading-relaxed ${getLayerStyle("description")}`}
                    data-layer-id={isEditable ? "description" : undefined}
                    data-layer-type={isEditable ? "text" : undefined}
                >
                    {isEditable ? (
                        <EditableText
                            value={data.description}
                            onChange={(v) => handleChange("description", v)}
                            placeholder="Add description..."
                            className="text-xl text-muted-foreground leading-relaxed"
                            multiline
                        />
                    ) : data.description}
                </p>
            )}
        </div>
    )
}
