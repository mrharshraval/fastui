"use client"

export function PublicTimelineSection({ data }) {
    if (!data?.events?.length) return null

    return (
        <div className="my-16 max-w-3xl mx-auto">
            <div className="border-l-2 border-muted pl-8 space-y-12">
                {data.events.map((event, index) => (
                    <div key={index} className="relative">
                        <div className="absolute -left-[41px] top-1 h-5 w-5 rounded-full border-4 border-background bg-primary" />
                        <div className="text-sm font-semibold text-primary mb-1">{event.date}</div>
                        <h3 className="text-xl font-bold mb-2">{event.title}</h3>
                        <p className="text-muted-foreground leading-relaxed">{event.description}</p>
                    </div>
                ))}
            </div>
        </div>
    )
}
