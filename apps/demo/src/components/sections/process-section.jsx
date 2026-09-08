"use client"

export function ProcessSection({ data, onDataChange, isEditable = false, layerState = {} }) {
    if (!data?.steps?.length) return null

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
                <div className="grid gap-12 lg:grid-cols-2 items-center">
                    <div
                        className={`space-y-8 ${getLayerStyle("content-col")}`}
                        data-layer-id={isEditable ? "content-col" : undefined}
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
                        <div
                            className={`space-y-8 ${getLayerStyle("steps")}`}
                            data-layer-id={isEditable ? "steps" : undefined}
                            data-layer-type={isEditable ? "list" : undefined}
                        >
                            {data.steps.map((step, i) => (
                                <div
                                    key={i}
                                    className={`flex gap-6 ${getLayerStyle(`step-${i}`)}`}
                                    data-layer-id={isEditable ? `step-${i}` : undefined}
                                    data-layer-type={isEditable ? "step" : undefined}
                                >
                                    <div className="flex-none">
                                        <span className="text-3xl font-bold text-muted-foreground/20">
                                            {String(i + 1).padStart(2, '0')}
                                        </span>
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-xl mb-2">{step.title}</h3>
                                        <p className="text-muted-foreground leading-relaxed">{step.description}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                    {data.image && (
                        <div
                            className={`relative h-[500px] rounded-xl overflow-hidden bg-secondary/30 hidden lg:block ${getLayerStyle("image-col")}`}
                            data-layer-id={isEditable ? "image-col" : undefined}
                            data-layer-type={isEditable ? "container" : undefined}
                        >
                            <div
                                className={`w-full h-full ${getLayerStyle("image")}`}
                                data-layer-id={isEditable ? "image" : undefined}
                                data-layer-type={isEditable ? "image" : undefined}
                            >
                                <img src={data.image} alt={data.title || "Process"} className="w-full h-full object-cover" />
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </section>
    )
}
