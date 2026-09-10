"use client"
import { Button } from "@/components/ui/button"
import Link from "next/link"

export function PublicCTASection({ data }) {
    if (!data?.title) return null

    return (
        <div className="my-12 relative rounded-2xl overflow-hidden bg-primary text-primary-foreground py-16 px-8 text-center">
            {data.backgroundImage && (
                <>
                    <div className="absolute inset-0 z-0">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                            src={data.backgroundImage}
                            alt=""
                            className="w-full h-full object-cover"
                        />
                    </div>
                    <div className="absolute inset-0 z-10 bg-primary/80" />
                </>
            )}

            <div className="relative z-20 max-w-2xl mx-auto space-y-6">
                <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
                    {data.title}
                </h2>
                {data.description && (
                    <p className="text-lg opacity-90 leading-relaxed">
                        {data.description}
                    </p>
                )}
                {data.buttonText && (
                    <Button asChild size="lg" variant="secondary" className="mt-4">
                        <Link href={data.buttonLink || "#"}>
                            {data.buttonText}
                        </Link>
                    </Button>
                )}
            </div>
        </div>
    )
}
