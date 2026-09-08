"use client"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Quote } from "lucide-react"

export function PublicTestimonialSection({ data }) {
    if (!data?.items?.length) return null

    return (
        <div className="my-16 grid grid-cols-1 md:grid-cols-2 gap-6">
            {data.items.map((item, index) => (
                <div key={index} className="p-6 rounded-2xl bg-muted/30 border relative">
                    <Quote className="h-8 w-8 text-muted-foreground/20 absolute top-6 right-6" />
                    <p className="text-lg italic leading-relaxed mb-6 text-foreground/90">
                        "{item.quote}"
                    </p>
                    <div className="flex items-center gap-4">
                        <Avatar>
                            <AvatarImage src={item.avatar} />
                            <AvatarFallback>{item.author?.[0]}</AvatarFallback>
                        </Avatar>
                        <div>
                            <div className="font-semibold">{item.author}</div>
                            <div className="text-sm text-muted-foreground">{item.role}</div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    )
}
