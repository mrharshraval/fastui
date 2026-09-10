import Image from "next/image"
import { Button } from "@/components/ui/button"
import { CheckCircle2 } from "lucide-react"
import { CTABanner } from "@/components/sections/cta-banner"

export default function AboutPage() {
    return (
        <main className="flex min-h-screen flex-col pt-24 pb-20 bg-background">
            <div className="container px-8 sm:px-4 md:px-12 space-y-16">
                {/* Header */}
                <div className="text-center max-w-3xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <div className="inline-flex items-center rounded-full bg-secondary px-3 py-1 text-sm font-medium text-secondary-foreground">
                        Our Mission
                    </div>
                    <h1 className="text-4xl md:text-7xl font-bold tracking-tighter text-foreground">
                        Redefining Dental Care
                    </h1>
                    <p className="text-xl text-muted-foreground leading-relaxed">
                        We combine advanced technology with a human touch to create the best dental experience possible.
                    </p>
                </div>
            </div>

            {/* Mission Section */}
            <section className="py-20 bg-background">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="grid gap-12 lg:grid-cols-2 items-center">
                        <div className="space-y-6 text-center lg:text-left">
                            <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">Our Mission</h2>
                            <p className="text-muted-foreground text-lg leading-relaxed">
                                At Brainlab, our mission is simple: to provide world-class dental care in a comfortable, modern environment. We believe that visiting the dentist should be a positive experience, not a chore.
                            </p>
                            <p className="text-muted-foreground text-lg leading-relaxed">
                                We invest in the latest technology and training to ensure that our treatments are precise, efficient, and minimally invasive. But more importantly, we invest in our people—building a team that truly cares about your well-being.
                            </p>
                            <div className="grid gap-4 sm:grid-cols-2 mt-8 justify-items-center sm:justify-items-start">
                                {["Advanced Technology", "Comfort-First Approach", "Expert Team", "Transparent Pricing"].map((item) => (
                                    <div key={item} className="flex items-center gap-2">
                                        <CheckCircle2 className="h-5 w-5 text-primary" />
                                        <span className="font-medium">{item}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="relative aspect-square lg:aspect-[4/3] rounded-2xl overflow-hidden border border-border/40">
                            {/* Placeholder for clinic interior */}
                            <div className="absolute inset-0 bg-muted flex items-center justify-center text-muted-foreground">
                                Clinic Interior Image
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Team Section */}
            <section className="py-20 bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="text-center max-w-2xl mx-auto mb-16 space-y-4">
                        <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">Meet Our Specialists</h2>
                        <p className="text-muted-foreground text-lg">
                            Our team of experienced dentists and hygienists is dedicated to your smile.
                        </p>
                    </div>
                    <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="group relative overflow-hidden rounded-[2rem] bg-secondary/30 transition-colors hover:bg-secondary/50">
                                <div className="aspect-[3/4] relative bg-muted/50">
                                    {/* Placeholder for doctor image */}
                                    <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
                                        Doctor {i} Photo
                                    </div>
                                </div>
                                <div className="p-8 space-y-2 text-center sm:text-left">
                                    <h3 className="font-bold text-xl text-foreground">Dr. Name Surname</h3>
                                    <p className="text-muted-foreground font-medium">Chief Dentist</p>
                                    <p className="text-sm text-muted-foreground leading-relaxed">
                                        Specializing in cosmetic dentistry and implants with over 10 years of experience.
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <CTABanner />
        </main>
    )
}
