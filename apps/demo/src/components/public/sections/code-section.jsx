"use client"

export function PublicCodeSection({ data }) {
    if (!data?.code) return null

    return (
        <div className="my-8 rounded-lg overflow-hidden border bg-zinc-950 text-white">
            <div className="flex items-center justify-between px-4 py-2 bg-zinc-900 border-b border-zinc-800">
                <span className="text-xs font-mono text-zinc-400">{data.language || "text"}</span>
                <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500/20" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500/20" />
                    <div className="w-3 h-3 rounded-full bg-green-500/20" />
                </div>
            </div>
            <pre className="p-4 overflow-x-auto text-sm font-mono leading-relaxed">
                <code>{data.code}</code>
            </pre>
        </div>
    )
}
