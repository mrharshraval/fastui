"use client"

import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Star, CheckCircle2, ArrowRight, Quote } from "lucide-react"
import Link from "next/link"
import { SmileGallery } from "@/components/sections/smile-gallery"
import { VideoTestimonialCarousel } from "@/components/sections/video-testimonial-carousel"
import { useDemo } from "@/lib/demo-context"
import { siteConfig } from "@/config/site"
import { CTABanner } from "@/components/sections/cta-banner"
import { MapSection } from "@/components/sections/map-section"

export default function TokenHome() {
    const { business, customization, demoLink } = useDemo()
    const clinicName = business?.name || siteConfig.name

    const headline = customization?.hero_headline || "Where healthy smiles begin."
    const subheadline = customization?.hero_subheadline || "Trusted dental care tailored to your family's needs."
    const heroImage = customization?.hero_image_url || "/hero_dentist_v1.png"

    // Authentic booking link or demo booking flow
    const bookingHref = customization?.booking_url && (customization.booking_url.startsWith("http://") || customization.booking_url.startsWith("https://"))
        ? customization.booking_url
        : demoLink("/book")

    // Authentic testimonials or fallback defaults
    const defaultTestimonials = [
        { name: "Sarah J.", text: "I used to be terrified of the dentist, but the gentle care made me feel so comfortable. My new veneers look amazing!" },
        { name: "Michael T.", text: "Professional, clean, and high-tech. I had my treatment done seamlessly without any discomfort. Highly recommend." },
        { name: "Emily R.", text: "Best dental experience I've ever had. The staff is friendly and the results of my clear aligner treatment are perfect." },
    ]
    const displayTestimonials = (customization?.testimonials && customization.testimonials.length > 0)
        ? customization.testimonials.slice(0, 3).map(t => ({ name: t.name || "Verified Patient", text: t.quote }))
        : defaultTestimonials

    return (
        <main className="flex flex-col relative -mt-[72px] md:-mt-[96px]">
            {/* Hero Section */}
            <section className="relative w-full pt-[calc(72px+2rem)] pb-16 md:pt-[calc(96px+3.5rem)] md:pb-20 lg:pt-[calc(96px+4.5rem)] lg:pb-24 bg-muted/30 overflow-hidden border-b border-border transition-colors">

                <div className="container relative z-10 px-4 sm:px-6 md:px-12 mx-auto">
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 xl:gap-16 items-center">
                        {/* Left Column: Content */}
                        <div className="lg:col-span-6 flex flex-col justify-center items-center text-center lg:items-start lg:text-left gap-6 max-w-3xl mx-auto lg:mx-0">
                            <div className="inline-flex items-center rounded-full border bg-background px-3 py-1 text-sm font-medium text-muted-foreground border-border w-fit">
                                Comprehensive Dental Care
                            </div>
                            <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none text-foreground text-center lg:text-left">
                                {headline}
                            </h1>
                            <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl text-center lg:text-left">
                                {subheadline}
                            </p>
                            <div className="pt-2 flex justify-center lg:justify-start w-full">
                                <Link href={bookingHref}>
                                    <Button size="lg" className="rounded-full h-12 px-8 text-base font-medium">
                                        Book appointment
                                    </Button>
                                </Link>
                            </div>
                        </div>

                        {/* Right Column: Hero Image */}
                        <div className="lg:col-span-6 w-full">
                            <div className="relative w-full aspect-[4/3] rounded-3xl overflow-hidden">
                                <Image
                                    src={heroImage}
                                    alt={`${clinicName} Modern Dental Care`}
                                    fill
                                    className="object-cover object-center"
                                    priority
                                    sizes="(min-width: 1024px) 50vw, 100vw"
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="w-full py-24 bg-muted md:bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="mb-16 space-y-4 text-center md:text-left">
                        <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">Why Choose {clinicName}?</h2>
                        <p className="text-muted-foreground text-lg max-w-2xl mx-auto md:mx-0">
                            We combine advanced technology with gentle, patient-first care to provide an exceptional dental experience.
                        </p>
                    </div>
                    <div className="grid gap-8 md:grid-cols-3">
                        {[
                            { title: "Advanced Technology", desc: "Digital X-rays, 3D imaging, and modern laser dentistry for precise, gentle care." },
                            { title: "Comfort-First Approach", desc: "Relaxing environment, transparent consultations, and gentle care for anxious patients." },
                            { title: "Expert Care Team", desc: "Highly trained specialists dedicated to your long-term oral health and confident smile." },
                        ].map((feature, i) => (
                            <div key={i} className="bg-background p-8 rounded-xl flex flex-col items-center text-center md:items-start md:text-left">
                                <div className="h-12 w-12 rounded-lg bg-background flex items-center justify-center text-foreground mb-6">
                                    <CheckCircle2 className="h-6 w-6" />
                                </div>
                                <h3 className="font-bold text-xl mb-3 text-foreground">{feature.title}</h3>
                                <p className="text-muted-foreground leading-relaxed">{feature.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Services Preview */}
            <section className="w-full py-24 bg-background">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="flex flex-col md:flex-row justify-between items-center md:items-end mb-12 gap-4 text-center md:text-left">
                        <div className="space-y-4 max-w-2xl mx-auto md:mx-0">
                            <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">Comprehensive Care</h2>
                            <p className="text-muted-foreground text-lg">
                                From routine checkups to complete smile transformations, we offer a full suite of modern treatments.
                            </p>
                        </div>
                        <Link href={demoLink("/treatments")} className="hidden md:flex items-center text-primary font-medium hover:underline">
                            View all treatments <ArrowRight className="ml-2 h-4 w-4" />
                        </Link>
                    </div>
                    <div className="grid gap-6 md:grid-cols-3">
                        {[
                            { title: "Cosmetic Dentistry", desc: "Veneers, whitening, and aesthetic bonding.", href: "/treatments/cosmetic" },
                            { title: "Dental Implants", desc: "Permanent, natural-looking solutions for missing teeth.", href: "/treatments/implants" },
                            { title: "Orthodontics", desc: "Clear aligners and comfortable modern braces.", href: "/treatments/orthodontics" },
                        ].map((service, i) => (
                            <Link key={i} href={demoLink(service.href)} className="group relative overflow-hidden rounded-xl bg-muted/50 p-8 flex flex-col justify-between items-center text-center md:items-start md:text-left h-full min-h-[220px]">
                                <div>
                                    <h3 className="font-bold text-2xl mb-3 text-foreground">{service.title}</h3>
                                    <p className="text-muted-foreground mb-6">{service.desc}</p>
                                </div>
                                <div className="flex items-center justify-center md:justify-start text-primary font-medium mt-auto group-hover:gap-2 transition-all">
                                    Read more <ArrowRight className="ml-2 h-4 w-4" />
                                </div>
                            </Link>
                        ))}
                    </div>
                    <div className="mt-8 md:hidden flex justify-center">
                        <Link href={demoLink("/treatments")} className="inline-flex items-center text-primary font-medium hover:underline">
                            View all treatments <ArrowRight className="ml-2 h-4 w-4" />
                        </Link>
                    </div>
                </div>
            </section>

            {/* Smile Gallery */}
            <SmileGallery />

            {/* Video Testimonials */}
            <section className="w-full py-24 bg-background">
                <div className="container px-8 sm:px-4 md:px-12">
                    <VideoTestimonialCarousel />
                </div>
            </section>

            {/* Testimonials */}
            <section className="w-full py-24 bg-muted md:bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl mb-16 text-center md:text-left">Patient Stories</h2>
                    <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
                        {displayTestimonials.map((testimonial, i) => (
                            <div key={i} className="bg-background p-8 rounded-xl relative flex flex-col items-center text-center md:items-start md:text-left">
                                <Quote className="absolute top-8 right-8 h-8 w-8 text-muted-foreground/20 hidden md:block" />
                                <div className="flex justify-center md:justify-start gap-1 mb-4">
                                    {[1, 2, 3, 4, 5].map((star) => (
                                        <Star key={star} className="h-4 w-4 fill-foreground text-foreground" />
                                    ))}
                                </div>
                                <p className="text-muted-foreground leading-relaxed mb-6">"{testimonial.text}"</p>
                                <p className="font-bold text-foreground">{testimonial.name}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Final CTA */}
            <CTABanner />

            {/* Location & Map Section */}
            <MapSection />
        </main>
    )
}
