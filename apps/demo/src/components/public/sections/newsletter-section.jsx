"use client"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export function PublicNewsletterSection({ data }) {
    if (!data?.title) return null
    return (
        <div className="my-16 py-12 px-6 rounded-2xl bg-muted text-center border border-border">
            <div className="max-w-xl mx-auto space-y-4">
                <h3 className="text-2xl font-bold">{data.title}</h3>
                <p className="text-muted-foreground">{data.description}</p>
                <div className="flex gap-2 max-w-sm mx-auto pt-4">
                    <Input placeholder={data.placeholder || "Enter your email"} className="bg-background" />
                    <Button>Subscribe</Button>
                </div>
            </div>
        </div>
    )
}
