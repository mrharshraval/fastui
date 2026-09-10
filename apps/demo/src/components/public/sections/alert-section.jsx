"use client"
import { AlertCircle, CheckCircle2, Info, XCircle } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

const VARIANTS = {
    default: { icon: Info, class: "border-primary/50 text-primary [&>svg]:text-primary" },
    success: { icon: CheckCircle2, class: "border-whatsapp/50 text-whatsapp [&>svg]:text-whatsapp" },
    warning: { icon: AlertCircle, class: "border-border text-foreground [&>svg]:text-foreground" },
    destructive: { icon: XCircle, class: "border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive" },
}

export function PublicAlertSection({ data }) {
    if (!data?.content && !data?.title) return null

    const variant = VARIANTS[data.variant || "default"]
    const Icon = variant.icon

    return (
        <div className="my-8">
            {/* Using standard Alert component styling or custom mapping */}
            <div className={`relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground ${variant.class}`}>
                <Icon className="h-4 w-4" />
                {data.title && <h5 className="mb-1 font-medium leading-none tracking-tight">{data.title}</h5>}
                <div className="text-sm [&_p]:leading-relaxed">
                    {data.content}
                </div>
            </div>
        </div>
    )
}
