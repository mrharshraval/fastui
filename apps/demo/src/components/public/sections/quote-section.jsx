"use client"
import { Quote } from "lucide-react"

export function PublicQuoteSection({ data }) {
    if (!data?.text) return null

    return (
        <blockquote className="my-12 relative p-8 pl-12 border-l-4 border-primary bg-muted/30 rounded-r-lg">
            <Quote className="absolute top-8 left-4 h-6 w-6 text-muted-foreground/40" />
            <p className="text-xl md:text-2xl font-serif italic leading-relaxed text-foreground">
                "{data.text}"
            </p>
            {data.author && (
                <footer className="mt-4 text-sm font-medium text-muted-foreground">
                    — {data.author}
                </footer>
            )}
        </blockquote>
    )
}
