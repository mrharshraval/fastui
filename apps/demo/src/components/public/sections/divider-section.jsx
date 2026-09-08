"use client"
import { Separator } from "@/components/ui/separator"

export function PublicDividerSection({ data }) {
    const style = data?.style || "solid"

    if (style === "gradient") {
        return <div className="h-px w-full bg-gradient-to-r from-transparent via-border to-transparent my-12" />
    }

    if (style === "dots") {
        return (
            <div className="flex items-center justify-center gap-2 my-12 text-muted-foreground/40">
                <div className="w-1.5 h-1.5 rounded-full bg-current" />
                <div className="w-1.5 h-1.5 rounded-full bg-current" />
                <div className="w-1.5 h-1.5 rounded-full bg-current" />
            </div>
        )
    }

    if (style === "dashed") {
        return <div className="w-full border-t border-dashed my-12" />
    }

    return <Separator className="my-12" />
}
