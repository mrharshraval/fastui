import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { MapPin, Phone, Mail, Clock } from "lucide-react"

export default function ContactPage() {
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
                        We are here to answer your questions and help you schedule your appointment. Reach out to us today.
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
                                            123 Dental Street, Suite 100<br />
                                            New York, NY 10001
                                        </p>
                                    </div>
                                </div>

                                <div className="flex items-start space-x-4">
                                    <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-card border border-border/50 shadow-sm text-foreground">
                                        <Phone className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold">Call Us</h3>
                                        <p className="text-muted-foreground">
                                            (555) 123-4567
                                        </p>
                                        <p className="text-sm text-muted-foreground mt-1">
                                            Mon-Fri: 9am - 6pm
                                        </p>
                                    </div>
                                </div>

                                <div className="flex items-start space-x-4">
                                    <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-card border border-border/50 shadow-sm text-foreground">
                                        <Mail className="h-5 w-5" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold">Email Us</h3>
                                        <p className="text-muted-foreground">
                                            hello@brainlab.com
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Map Placeholder */}
                        <div className="aspect-video w-full rounded-[2rem] bg-secondary/30 overflow-hidden relative">
                            <div className="absolute inset-0 flex items-center justify-center text-muted-foreground font-medium">
                                Google Maps Integration
                            </div>
                        </div>
                    </div>

                    {/* Contact Form */}
                    <div className="rounded-[2rem] bg-secondary/30 p-8">
                        <h2 className="text-2xl font-bold mb-6">Send us a Message</h2>
                        <form className="space-y-6">
                            <div className="grid gap-4 sm:grid-cols-2">
                                <div className="space-y-2">
                                    <label htmlFor="first-name" className="text-sm font-medium">First name</label>
                                    <Input id="first-name" placeholder="John" />
                                </div>
                                <div className="space-y-2">
                                    <label htmlFor="last-name" className="text-sm font-medium">Last name</label>
                                    <Input id="last-name" placeholder="Doe" />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label htmlFor="email" className="text-sm font-medium">Email</label>
                                <Input id="email" placeholder="john@example.com" type="email" />
                            </div>
                            <div className="space-y-2">
                                <label htmlFor="phone" className="text-sm font-medium">Phone</label>
                                <Input id="phone" placeholder="(555) 123-4567" type="tel" />
                            </div>
                            <div className="space-y-2">
                                <label htmlFor="message" className="text-sm font-medium">Message</label>
                                <Textarea id="message" placeholder="How can we help you?" className="min-h-[150px]" />
                            </div>
                            <Button type="submit" className="w-full rounded-full bg-primary hover:bg-primary/90 text-primary-foreground h-12 text-base font-medium shadow-lg hover:shadow-xl transition-all hover:scale-[1.02]">
                                Send Message
                            </Button>
                        </form>
                    </div>
                </div>
            </div>
        </main>
    )
}
