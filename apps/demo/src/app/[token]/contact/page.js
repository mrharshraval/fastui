"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { MapPin, Phone, Mail, Clock, CheckCircle2 } from "lucide-react"
import { Icons } from "@/components/icons"
import { useDemo } from "@/lib/demo-context"
import { trackDemoEvent } from "@/lib/demo-api"
import { siteConfig } from "@/config/site"

export default function TokenContactPage() {
    const { business, customization, token } = useDemo()
    const clinicName = business?.name || siteConfig.name
    const cityState = [business?.city, business?.state, business?.postal_code].filter(Boolean).join(", ")
    const fullAddress = [business?.address, cityState].filter(Boolean).join(", ")

    const [isSubmitted, setIsSubmitted] = React.useState(false)
    const [isLoading, setIsLoading] = React.useState(false)

    const mapQuery = encodeURIComponent(
        [business?.name, business?.address, business?.city].filter(Boolean).join(", ") || "Dental Clinic, Ahmedabad"
    )

    const handleSubmit = async (e) => {
        e.preventDefault()
        setIsLoading(true)
        try {
            if (token) {
                await trackDemoEvent(token, {
                    event_type: "cta_clicked",
                    metadata: { action: "contact_form_submitted" },
                })
            }
            setIsSubmitted(true)
        } catch {
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <main className="flex min-h-screen flex-col pt-24 pb-20">
            <div className="container px-8 sm:px-4 md:px-12">
                {/* Header */}
                <div className="text-center max-w-3xl mx-auto space-y-6 mb-16 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <div className="inline-flex items-center rounded-full bg-secondary px-3 py-1 text-sm font-medium text-secondary-foreground">
                        Contact Us
                    </div>
                    <h1 className="text-4xl md:text-7xl font-bold tracking-tighter text-foreground">Get in Touch</h1>
                    <p className="text-xl text-muted-foreground leading-relaxed">
                        We are here to answer your questions and help you schedule your appointment with {clinicName}. Reach out to us today.
                    </p>
                </div>

                <div className="grid gap-12 lg:grid-cols-2">
                    {/* Contact Info */}
                    <div className="space-y-8">
                        <div className="rounded-[2rem] bg-secondary/30 p-8 space-y-8">
                            <h2 className="text-2xl font-bold">Contact Information</h2>

                            <div className="space-y-6">
                                <div className="flex items-start space-x-4">
                                    <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-card border border-border/50 shadow-sm text-foreground">
                                        <MapPin className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold">Visit Us</h3>
                                        <p className="text-muted-foreground">
                                            {business?.address || "Medical Square"}<br />
                                            {cityState || "Ahmedabad, Gujarat"}
                                        </p>
                                    </div>
                                </div>

                                {business?.phone && (
                                    <div className="flex items-start space-x-4">
                                        <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-card border border-border/50 shadow-sm text-foreground">
                                            <Phone className="h-5 w-5" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold">Call Us</h3>
                                            <p className="text-muted-foreground">
                                                <a href={`tel:${business.phone}`} className="hover:underline">
                                                    {business.phone}
                                                </a>
                                            </p>
                                            <p className="text-sm text-muted-foreground mt-1">
                                                {business?.opening_hours || "Mon-Sat: 9:00 AM - 8:00 PM"}
                                            </p>
                                        </div>
                                    </div>
                                )}

                                {(business?.whatsapp || customization?.whatsapp_url) && (
                                    <div className="flex items-start space-x-4">
                                        <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-whatsapp/10 text-whatsapp shadow-sm">
                                            <Icons.whatsapp className="h-5 w-5 fill-current" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold">WhatsApp</h3>
                                            <p className="text-muted-foreground">
                                                <a
                                                    href={customization?.whatsapp_url || (business?.whatsapp?.startsWith("http") ? business.whatsapp : `https://wa.me/${(business?.whatsapp || business?.phone || "").replace(/\D/g, "")}`)}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-whatsapp font-medium hover:underline inline-flex items-center gap-1"
                                                >
                                                    Chat on WhatsApp
                                                </a>
                                            </p>
                                            <p className="text-sm text-muted-foreground mt-1">
                                                {business?.whatsapp || business?.phone}
                                            </p>
                                        </div>
                                    </div>
                                )}

                                {business?.email && (
                                    <div className="flex items-start space-x-4">
                                        <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-card border border-border/50 shadow-sm text-foreground">
                                            <Mail className="h-5 w-5" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold">Email Us</h3>
                                            <p className="text-muted-foreground">
                                                <a href={`mailto:${business.email}`} className="hover:underline">
                                                    {business.email}
                                                </a>
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Interactive Google Map Embed */}
                        <div className="aspect-video w-full rounded-[2rem] bg-secondary/30 overflow-hidden relative shadow-sm border border-border/40">
                            <iframe
                                title={`${clinicName} Location`}
                                width="100%"
                                height="100%"
                                style={{ border: 0 }}
                                loading="lazy"
                                allowFullScreen
                                src={`https://maps.google.com/maps?q=${mapQuery}&t=&z=15&ie=UTF8&iwloc=&output=embed`}
                            />
                        </div>
                    </div>

                    {/* Contact Form */}
                    <div className="rounded-[2rem] bg-secondary/30 p-8 flex flex-col justify-center">
                        <h2 className="text-2xl font-bold mb-6">Send us a Message</h2>
                        {isSubmitted ? (
                            <div className="py-12 text-center space-y-4 animate-in fade-in zoom-in-95 duration-300">
                                <div className="size-12 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto">
                                    <CheckCircle2 className="size-7" />
                                </div>
                                <h3 className="text-xl font-bold tracking-tight text-foreground">
                                    Message Sent!
                                </h3>
                                <p className="text-muted-foreground text-sm max-w-sm mx-auto leading-relaxed">
                                    Thank you! In your live website, inquiries are delivered instantly to your team dashboard and email.
                                </p>
                                <Button
                                    variant="outline"
                                    onClick={() => setIsSubmitted(false)}
                                    className="rounded-full mt-2"
                                >
                                    Send Another Message
                                </Button>
                            </div>
                        ) : (
                            <form onSubmit={handleSubmit} className="space-y-6">
                                <div className="grid gap-4 sm:grid-cols-2">
                                    <div className="space-y-2">
                                        <label htmlFor="first-name" className="text-sm font-medium">First name</label>
                                        <Input id="first-name" placeholder="John" required />
                                    </div>
                                    <div className="space-y-2">
                                        <label htmlFor="last-name" className="text-sm font-medium">Last name</label>
                                        <Input id="last-name" placeholder="Doe" required />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <label htmlFor="email" className="text-sm font-medium">Email</label>
                                    <Input id="email" placeholder="john@example.com" type="email" required />
                                </div>
                                <div className="space-y-2">
                                    <label htmlFor="phone" className="text-sm font-medium">Phone</label>
                                    <Input id="phone" placeholder="+91 98765 43210" type="tel" required />
                                </div>
                                <div className="space-y-2">
                                    <label htmlFor="message" className="text-sm font-medium">Message</label>
                                    <Textarea id="message" placeholder="How can we help you?" className="min-h-[120px]" required />
                                </div>
                                <Button type="submit" disabled={isLoading} className="w-full rounded-full h-11">
                                    {isLoading ? "Sending..." : "Send Message"}
                                </Button>
                            </form>
                        )}
                    </div>
                </div>
            </div>
        </main>
    )
}
