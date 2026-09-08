"use client"

import * as React from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { CheckCircle2, ArrowRight, ShieldCheck } from "lucide-react"
import { useDemo } from "@/lib/demo-context"
import { CTABanner } from "@/components/sections/cta-banner"

const TREATMENT_DETAILS = {
    cosmetic: {
        category: "Cosmetic Dentistry",
        headline: "Design your perfect smile.",
        subheadline: "From subtle improvements to complete smile transformations, our aesthetic dental treatments boost your confidence.",
        solutions: [
            {
                title: "Porcelain Veneers",
                desc: "Custom-crafted ceramic shells bonded to the front of your teeth to correct chips, stains, and gaps.",
                features: ["Stain resistant", "Natural translucency", "Long-lasting finish"]
            },
            {
                title: "Professional Teeth Whitening",
                desc: "In-office clinical brightening that safely removes deep discoloration in a single session.",
                features: ["Immediate results", "Enamel safe", "Personalized shade match"]
            },
            {
                title: "Composite Dental Bonding",
                desc: "Sculpted tooth-colored composite resin to repair small fractures and reshape uneven edges.",
                features: ["Single-visit treatment", "Cost effective", "Minimally invasive"]
            }
        ]
    },
    orthodontics: {
        category: "Orthodontics",
        headline: "A straight, harmonious smile.",
        subheadline: "Modern teeth straightening for teenagers and adults using clear aligners and comfortable braces.",
        solutions: [
            {
                title: "Clear Aligners",
                desc: "Virtually invisible, custom-molded aligners that discreetly shift your teeth into proper alignment.",
                features: ["Removable for meals", "Zero metal brackets", "Easy oral hygiene"]
            },
            {
                title: "Modern Braces",
                desc: "Low-profile ceramic and metal braces providing reliable, predictable bite and teeth correction.",
                features: ["Handles complex bites", "Fast progress", "Comfort-engineered"]
            },
            {
                title: "Retainers & Stability",
                desc: "Custom nighttime retainers to safeguard and preserve your smile alignment for life.",
                features: ["Custom molded", "Durable materials", "Nightly wear"]
            }
        ]
    },
    implants: {
        category: "Dental Implants",
        headline: "Permanent solutions for missing teeth.",
        subheadline: "Restore full chewing function, jawbone health, and natural aesthetics with medical-grade titanium implants.",
        solutions: [
            {
                title: "Single Tooth Implants",
                desc: "A permanent titanium root topped with an aesthetic porcelain crown that looks and feels like a real tooth.",
                features: ["Lifelong durability", "Preserves adjacent teeth", "Natural bite force"]
            },
            {
                title: "Implant-Supported Bridges",
                desc: "Stable bridges anchored to implants to replace several consecutive missing teeth seamlessly.",
                features: ["No loose dentures", "High structural strength", "Cost-efficient replacement"]
            },
            {
                title: "Full-Arch Restoration",
                desc: "State-of-the-art permanent arch rehabilitation anchored on four to six strategic implants.",
                features: ["Same-day provisional teeth", "Restores full chewing", "Rejuvenates facial profile"]
            }
        ]
    },
    general: {
        category: "General Dentistry",
        headline: "The foundation of a healthy smile.",
        subheadline: "Preventive care, thorough cleanings, and routine treatments to keep your teeth and gums healthy for life.",
        solutions: [
            {
                title: "Exams & Ultrasonic Cleanings",
                desc: "Comprehensive oral health checkups, digital X-rays, and gentle tartar removal to prevent periodontal issues.",
                features: ["Gum health assessment", "Oral screening", "Enamel polishing"]
            },
            {
                title: "Tooth-Colored Fillings",
                desc: "Durable composite resin restorations matched to your tooth shade to seal cavities discreetly.",
                features: ["Mercury-free", "Blends naturally", "Preserves tooth structure"]
            },
            {
                title: "Root Canal Therapy",
                desc: "Gentle, modern endodontic therapy that relieves infection and preserves your natural tooth.",
                features: ["Immediate pain relief", "Saves natural tooth", "High success rate"]
            }
        ]
    },
    pediatric: {
        category: "Pediatric Dentistry",
        headline: "Gentle dental care for young smiles.",
        subheadline: "Creating positive, stress-free dental experiences for infants, children, and teenagers.",
        solutions: [
            {
                title: "Children's Dental Exams",
                desc: "Fun, friendly dental visits focused on tracking tooth development and building confident habits.",
                features: ["Patience-first approach", "Kid-friendly language", "Positive reinforcement"]
            },
            {
                title: "Fluoride & Dental Sealants",
                desc: "Protective shield coatings applied to the chewing surfaces of molars to prevent cavities.",
                features: ["Quick application", "Pain-free", "Lasts several years"]
            },
            {
                title: "Gentle Restorations",
                desc: "Child-sized composite fillings and crowns designed specifically for primary teeth.",
                features: ["Minimally invasive", "Comfort focused", "Protects adult teeth"]
            }
        ]
    },
    emergency: {
        category: "Emergency Dental Care",
        headline: "Fast relief when you need it most.",
        subheadline: "Prompt emergency appointments for severe toothaches, broken teeth, and sudden dental trauma.",
        solutions: [
            {
                title: "Acute Toothache Relief",
                desc: "Rapid diagnostic evaluation and palliative intervention to stop intense dental pain.",
                features: ["Same-day priority", "Gentle diagnosis", "Infection control"]
            },
            {
                title: "Broken or Chipped Tooth Repair",
                desc: "Immediate cosmetic bonding or emergency crowns to protect the exposed nerve and restore function.",
                features: ["Functional restoration", "Aesthetic matching", "Prevents further fracture"]
            },
            {
                title: "Lost Fillings & Crowns",
                desc: "Swift re-cementation or placement of temporary restorations to safeguard vulnerable teeth.",
                features: ["Fast turnaround", "Stops sensitivity", "Protects tooth integrity"]
            }
        ]
    },
    surgical: {
        category: "Oral Surgery",
        headline: "Precision surgical dental care.",
        subheadline: "Minimally invasive extractions, wisdom tooth removal, and bone regeneration with gentle anesthesia.",
        solutions: [
            {
                title: "Wisdom Teeth Extraction",
                desc: "Careful removal of impacted or crowded third molars to prevent pain, cyst formation, and misalignment.",
                features: ["Local anesthesia & sedation", "Precision 3D imaging", "Smooth recovery plan"]
            },
            {
                title: "Bone Grafting",
                desc: "Restoring jawbone volume and density to provide a solid foundation for future dental implants.",
                features: ["Biocompatible materials", "Outpatient procedure", "Essential for implants"]
            },
            {
                title: "Soft Tissue Procedures",
                desc: "Gentle gum contouring and frenectomy procedures performed with high-precision instruments.",
                features: ["Minimal bleeding", "Fast healing", "Improves aesthetics"]
            }
        ]
    },
    invisalign: {
        category: "Invisalign",
        headline: "Clear, discreet teeth alignment.",
        subheadline: "Straighten your teeth comfortably with virtually invisible, removable custom aligners.",
        solutions: [
            {
                title: "Custom 3D Treatment Plan",
                desc: "Digital scanning captures exact teeth positions to map out each microscopic movement before starting.",
                features: ["Zero messy impressions", "Preview smile outcome", "Predictable roadmap"]
            },
            {
                title: "Smooth SmartTrack Aligners",
                desc: "Medical-grade clear plastic aligners engineered for comfortable tooth movement and easy removal.",
                features: ["Eat whatever you like", "Discreet in photos", "No wire emergencies"]
            },
            {
                title: "Personalized Monitoring",
                desc: "Regular check-ins with our dental team to track progress and provide new aligner sets.",
                features: ["Flexible visits", "Progress verification", "Doctor-supervised"]
            }
        ]
    }
}

export default function TokenTreatmentDetail() {
    const params = useParams()
    const slug = (params?.slug || "general").toLowerCase()
    const { demoLink } = useDemo()

    const details = TREATMENT_DETAILS[slug] || TREATMENT_DETAILS.general

    return (
        <main className="flex flex-col min-h-screen bg-background">
            {/* Hero Section */}
            <section className="w-full py-24 bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="flex flex-col items-center text-center md:items-start md:text-left gap-6 max-w-3xl mx-auto md:mx-0">
                        <div className="inline-flex items-center rounded-full border bg-background px-3 py-1 text-sm font-medium text-muted-foreground border-border w-fit">
                            {details.category}
                        </div>
                        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none text-foreground text-center md:text-left">
                            {details.headline}
                        </h1>
                        <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl text-center md:text-left">
                            {details.subheadline}
                        </p>
                        <div className="flex justify-center md:justify-start gap-4 pt-4 w-full">
                            <Link href={demoLink("/book")}>
                                <Button size="lg" className="rounded-full h-12 px-8 text-base font-medium">
                                    Book Consultation
                                </Button>
                            </Link>
                        </div>
                    </div>
                </div>
            </section>

            {/* Solutions Grid */}
            <section className="w-full py-24 bg-background">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="mb-16 text-center md:text-left">
                        <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl mb-4">Our Clinical Solutions</h2>
                        <p className="text-muted-foreground text-lg max-w-2xl mx-auto md:mx-0">
                            Tailored treatments designed around your comfort, oral biology, and long-term health.
                        </p>
                    </div>
                    <div className="grid gap-8 md:grid-cols-3">
                        {details.solutions.map((item, i) => (
                            <div key={i} className="bg-secondary/30 p-8 rounded-xl hover:bg-secondary/50 transition-colors group flex flex-col justify-between items-center text-center md:items-start md:text-left">
                                <div className="flex flex-col items-center md:items-start w-full">
                                    <h3 className="font-bold text-2xl mb-4 text-foreground">{item.title}</h3>
                                    <p className="text-muted-foreground mb-6 leading-relaxed">
                                        {item.desc}
                                    </p>
                                    <ul className="space-y-3 mb-6 inline-block text-left">
                                        {item.features.map((feature, j) => (
                                            <li key={j} className="flex items-center text-sm text-muted-foreground">
                                                <CheckCircle2 className="h-4 w-4 mr-2 text-primary shrink-0" />
                                                {feature}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                                <Link href={demoLink("/book")} className="inline-flex items-center text-primary font-medium text-sm hover:underline mt-auto">
                                    Schedule inquiry <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                                </Link>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA */}
            <CTABanner />
        </main>
    )
}
