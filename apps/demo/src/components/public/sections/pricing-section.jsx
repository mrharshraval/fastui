"use client"
import { Check } from "lucide-react"
import { Button } from "@/components/ui/button"

export function PublicPricingSection({ data }) {
    if (!data?.plans?.length) return null

    return (
        <div className="my-16 grid grid-cols-1 md:grid-cols-3 gap-8">
            {data.plans.map((plan, index) => {
                const features = plan.features?.split(',').map(f => f.trim()).filter(Boolean) || []

                return (
                    <div key={index} className="flex flex-col p-6 border rounded-xl bg-card shadow-sm hover:shadow-md transition-shadow">
                        <div className="mb-4">
                            <h3 className="text-lg font-semibold">{plan.name}</h3>
                            <div className="text-3xl font-bold mt-2">{plan.price}</div>
                        </div>
                        <ul className="flex-1 space-y-3 mb-6">
                            {features.map((feature, i) => (
                                <li key={i} className="flex items-center text-sm text-muted-foreground">
                                    <Check className="h-4 w-4 mr-2 text-primary" />
                                    {feature}
                                </li>
                            ))}
                        </ul>
                        <Button className="w-full">Choose Plan</Button>
                    </div>
                )
            })}
        </div>
    )
}
