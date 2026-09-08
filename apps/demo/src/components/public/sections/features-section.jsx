"use client"
import { CheckCircle2, Star, Zap, Shield, Heart } from "lucide-react"

const ICONS = {
    star: Star,
    zap: Zap,
    shield: Shield,
    heart: Heart,
    check: CheckCircle2
}

export function PublicFeaturesSection({ data }) {
    if (!data?.features?.length) return null

    return (
        <div className="my-16 grid grid-cols-1 md:grid-cols-3 gap-8">
            {data.features.map((feature, index) => {
                const Icon = ICONS[feature.icon] || Star
                return (
                    <div key={index} className="flex flex-col items-start gap-4 p-6 rounded-xl border bg-card/50">
                        <div className="p-3 rounded-lg bg-primary/10 text-primary">
                            <Icon className="h-6 w-6" />
                        </div>
                        <div className="space-y-2">
                            <h3 className="font-semibold text-xl">{feature.title}</h3>
                            <p className="text-muted-foreground leading-relaxed">
                                {feature.description}
                            </p>
                        </div>
                    </div>
                )
            })}
        </div>
    )
}
