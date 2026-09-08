"use client"

import Image from "next/image"

export function TeamSection({ data, onDataChange, isEditable = false, layerState = {} }) {
    if (!data?.members?.length) return null

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
            className={`py-20 bg-muted/30 ${getLayerStyle("container")}`}
            data-layer-id={isEditable ? "container" : undefined}
            data-layer-type={isEditable ? "section" : undefined}
        >
            <div className="container px-8 sm:px-4 md:px-12">
                {(data.title || data.description) && (
                    <div
                        className={`text-center max-w-2xl mx-auto mb-16 space-y-4 ${getLayerStyle("header")}`}
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
                                className={`text-muted-foreground text-lg ${getLayerStyle("description")}`}
                                data-layer-id={isEditable ? "description" : undefined}
                                data-layer-type={isEditable ? "text" : undefined}
                            >
                                {data.description}
                            </p>
                        )}
                    </div>
                )}
                <div
                    className={`grid gap-8 sm:grid-cols-2 lg:grid-cols-3 ${getLayerStyle("grid")}`}
                    data-layer-id={isEditable ? "grid" : undefined}
                    data-layer-type={isEditable ? "grid" : undefined}
                >
                    {data.members.map((member, i) => (
                        <div
                            key={i}
                            className={`group relative overflow-hidden rounded-[2rem] bg-secondary/30 transition-colors hover:bg-secondary/50 ${getLayerStyle(`member-${i}`)}`}
                            data-layer-id={isEditable ? `member-${i}` : undefined}
                            data-layer-type={isEditable ? "card" : undefined}
                        >
                            <div className="aspect-[3/4] relative bg-white/50">
                                {member.image ? (
                                    <Image
                                        src={member.image}
                                        alt={member.name || "Team member"}
                                        fill
                                        className="object-cover"
                                    />
                                ) : (
                                    <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
                                        Photo
                                    </div>
                                )}
                            </div>
                            <div className="p-8 space-y-2">
                                <h3 className="font-bold text-xl text-foreground">{member.name}</h3>
                                {member.role && (
                                    <p className="text-muted-foreground font-medium">{member.role}</p>
                                )}
                                {member.bio && (
                                    <p className="text-sm text-muted-foreground leading-relaxed">{member.bio}</p>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    )
}
