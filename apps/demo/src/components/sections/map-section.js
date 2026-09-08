"use client"

import * as React from "react"
import { useDemo } from "@/lib/demo-context"
import { siteConfig } from "@/config/site"

export function MapSection() {
    let business = null
    try {
        const demo = useDemo()
        business = demo?.business
    } catch {
        // Outside demo provider fallback
    }

    const clinicName = business?.name || siteConfig.name
    const mapQuery = encodeURIComponent(
        [business?.name, business?.address, business?.city].filter(Boolean).join(", ") || `${clinicName}, Ahmedabad`
    )

    return (
        <section className="w-full pb-16 md:pb-24 bg-background">
            <div className="container px-4 sm:px-6 md:px-12 mx-auto">
                <div className="w-full h-[380px] sm:h-[440px] md:h-[500px] rounded-3xl overflow-hidden border border-border/40 bg-muted">
                    <iframe
                        title={`${clinicName} Location Map`}
                        width="100%"
                        height="100%"
                        style={{ border: 0 }}
                        loading="lazy"
                        allowFullScreen
                        referrerPolicy="no-referrer-when-downgrade"
                        src={`https://maps.google.com/maps?q=${mapQuery}&t=&z=15&ie=UTF8&iwloc=&output=embed`}
                    />
                </div>
            </div>
        </section>
    )
}
