"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useDemo } from "@/lib/demo-context"
import { trackDemoEvent } from "@/lib/demo-api"
import { CheckCircle2 } from "lucide-react"

export function BookingForm({ className, ...props }) {
    const [isLoading, setIsLoading] = React.useState(false)
    const [isSubmitted, setIsSubmitted] = React.useState(false)
    const { token, business } = useDemo()

    async function onSubmit(event) {
        event.preventDefault()
        setIsLoading(true)

        const formData = new FormData(event.currentTarget)
        const data = {
            name: formData.get("name"),
            email: formData.get("email"),
            phone: formData.get("phone"),
            treatment: formData.get("treatment"),
            date: formData.get("date"),
            message: formData.get("message"),
        }

        try {
            if (token) {
                await trackDemoEvent(token, {
                    event_type: "cta_clicked",
                    metadata: { action: "booking_requested", treatment: data.treatment },
                })
            }
            setIsSubmitted(true)
            event.target.reset()
        } catch (error) {
            console.error("Booking submission error:", error)
        } finally {
            setIsLoading(false)
        }
    }

    if (isSubmitted) {
        return (
            <div className="py-12 px-4 text-center space-y-4 animate-in fade-in zoom-in-95 duration-300">
                <div className="size-14 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto">
                    <CheckCircle2 className="size-8" />
                </div>
                <h3 className="text-2xl font-bold tracking-tight text-foreground">
                    Appointment Request Received!
                </h3>
                <p className="text-muted-foreground text-sm max-w-md mx-auto leading-relaxed">
                    Thank you! On your live website, appointment requests are sent instantly to your clinic WhatsApp, email, and front-desk team.
                </p>
                <Button
                    variant="outline"
                    onClick={() => setIsSubmitted(false)}
                    className="rounded-full mt-2"
                >
                    Book Another Visit
                </Button>
            </div>
        )
    }

    return (
        <form onSubmit={onSubmit} className={cn("grid gap-6", className)} {...props}>
            <div className="grid gap-2">
                <label htmlFor="name" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                    Full Name
                </label>
                <input
                    id="name"
                    name="name"
                    placeholder="John Doe"
                    required
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="grid gap-2">
                    <label htmlFor="email" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                        Email
                    </label>
                    <input
                        id="email"
                        name="email"
                        placeholder="name@example.com"
                        type="email"
                        autoCapitalize="none"
                        autoComplete="email"
                        autoCorrect="off"
                        required
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                </div>
                <div className="grid gap-2">
                    <label htmlFor="phone" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                        Phone Number
                    </label>
                    <input
                        id="phone"
                        name="phone"
                        placeholder="+91 98765 43210"
                        type="tel"
                        required
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="grid gap-2">
                    <label htmlFor="treatment" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                        Treatment Type
                    </label>
                    <select
                        id="treatment"
                        name="treatment"
                        defaultValue=""
                        required
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        <option value="" disabled>Select a treatment</option>
                        <option value="general">General Dentistry</option>
                        <option value="pediatric">Pediatric Care</option>
                        <option value="surgical">Surgical / Wisdom Teeth</option>
                        <option value="cosmetic">Cosmetic Dentistry</option>
                        <option value="orthodontics">Orthodontics</option>
                        <option value="implants">Dental Implants</option>
                        <option value="other">Other / Consultation</option>
                    </select>
                </div>
                <div className="grid gap-2">
                    <label htmlFor="date" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                        Preferred Date
                    </label>
                    <input
                        id="date"
                        name="date"
                        type="date"
                        required
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                </div>
            </div>

            <div className="grid gap-2">
                <label htmlFor="message" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                    Additional Notes (Optional)
                </label>
                <textarea
                    id="message"
                    name="message"
                    placeholder="Tell us about your dental needs..."
                    className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
            </div>

            <Button type="submit" disabled={isLoading} className="w-full md:w-auto md:self-start rounded-full">
                {isLoading ? "Submitting..." : "Request Appointment"}
            </Button>
        </form>
    )
}
