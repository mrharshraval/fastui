"use client"

export function PublicStatsSection({ data }) {
    if (!data?.items?.length) return null

    return (
        <div className="my-16 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {data.items.map((item, index) => (
                <div key={index} className="space-y-2">
                    <div className="text-4xl md:text-5xl font-bold tracking-tight text-primary">
                        {item.value}
                        <span className="text-2xl md:text-3xl text-muted-foreground ml-1 font-normal">{item.suffix}</span>
                    </div>
                    <div className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
                        {item.label}
                    </div>
                </div>
            ))}
        </div>
    )
}
