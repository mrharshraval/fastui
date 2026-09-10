"use client"

export function PublicCodeSection({ data }) {
    if (!data?.code) return null

    return (
        <div className="my-8 rounded-lg overflow-hidden border bg-card text-card-foreground">
            <div className="flex items-center justify-between px-4 py-2 bg-muted/60 border-b border-border">
                <span className="text-xs font-mono text-muted-foreground">{data.language || "text"}</span>
                <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-border" />
                    <div className="w-3 h-3 rounded-full bg-border" />
                    <div className="w-3 h-3 rounded-full bg-border" />
                </div>
            </div>
            <pre className="p-4 overflow-x-auto text-sm font-mono leading-relaxed">
                <code>{data.code}</code>
            </pre>
        </div>
    )
}
