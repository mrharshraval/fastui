"use client"

import Image from "next/image"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { CheckCircle2 } from "lucide-react"
import { useDemo } from "@/lib/demo-context"
import { siteConfig } from "@/config/site"
import { CTABanner } from "@/components/sections/cta-banner"

export default function TokenAboutPage() {
    const { business, customization, demoLink } = useDemo()
    const clinicName = business?.name || siteConfig.name

    const doctorName = customization?.doctor_name || "Dr. Sarah Jenkins"
    const doctorTitle = customization?.doctor_title || "Chief Dental Surgeon"
    const doctorBio = customization?.doctor_bio || "Specializing in cosmetic dentistry, dental implants, and compassionate preventive dental care with over 10 years of clinical experience."
    const doctorPhoto = customization?.doctor_photo_url || "/female_dentist_portrait_1.png"
    const interiorPhoto = customization?.clinic_interior_url || "/hero_dentist_v1.png"

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
                                {customization?.about_text || `At ${clinicName}, our mission is simple: to provide world-class dental care in a comfortable, modern environment. We believe that visiting the dentist should be a positive experience, not a chore.`}
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
                            <Image
                                src={interiorPhoto}
                                alt={`${clinicName} Modern Clinic`}
                                fill
                                className="object-cover"
                                sizes="(max-width: 768px) 100vw, 50vw"
                            />
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
                    <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3 max-w-5xl mx-auto">
                        {((customization?.doctors && customization.doctors.length > 0)
                            ? customization.doctors.slice(0, 3).map((d, i) => ({
                                name: d.name,
                                title: d.title || (i === 0 ? doctorTitle : "Dental Specialist"),
                                bio: d.bio || (i === 0 ? doctorBio : "Committed to delivering gentle, patient-centered clinical excellence."),
                                photo_url: d.photo_url || (i === 0 ? doctorPhoto : (i === 1 ? "/female_dentist_portrait_2.png" : "/female_dentist_portrait_1.png")),
                            }))
                            : [
                                { name: doctorName, title: doctorTitle, bio: doctorBio, photo_url: doctorPhoto },
                                { name: "Dr. Elena Rostova", title: "Orthodontic Specialist", bio: "Certified clear aligner specialist focusing on non-invasive smile alignment and bite correction.", photo_url: "/female_dentist_portrait_2.png" },
                                { name: "Dr. David Chen", title: "Pediatric & Preventive Care", bio: "Creating gentle, friendly experiences for young patients and building lifelong oral health habits.", photo_url: "/female_dentist_portrait_1.png" },
                            ]
                        ).map((doc, i) => (
                            <div key={i} className={`group relative overflow-hidden rounded-[2rem] bg-secondary/30 transition-colors hover:bg-secondary/50 ${i === 2 ? "sm:col-span-2 lg:col-span-1" : ""}`}>
                                <div className="aspect-[3/4] relative bg-muted/50 overflow-hidden">
                                    <Image
                                        src={doc.photo_url}
                                        alt={doc.name}
                                        fill
                                        className="object-cover object-top group-hover:scale-105 transition-transform duration-500"
                                        sizes="(max-width: 768px) 100vw, 33vw"
                                    />
                                </div>
                                <div className="p-8 space-y-2 text-center sm:text-left">
                                    <h3 className="font-bold text-xl text-foreground">{doc.name}</h3>
                                    <p className="text-muted-foreground font-medium">{doc.title}</p>
                                    <p className="text-sm text-muted-foreground leading-relaxed">
                                        {doc.bio}
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
