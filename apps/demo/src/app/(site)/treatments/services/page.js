import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Sparkles, Smile, Hammer, Stethoscope, ArrowRight } from "lucide-react"
import { CTABanner } from "@/components/sections/cta-banner"

const services = [
    {
        title: "Cosmetic Dentistry",
        description: "Transform your smile with veneers, whitening, and bonding. We design smiles that look natural and radiant.",
        icon: Sparkles,
        href: "/services/cosmetic",
        color: "text-purple-500",
        bg: "bg-purple-500/10",
    },
    {
        title: "Orthodontics",
        description: "Straighten your teeth with modern braces or clear aligners like Invisalign. Perfect for all ages.",
        icon: Smile,
        href: "/services/orthodontics",
        color: "text-blue-500",
        bg: "bg-blue-500/10",
    },
    {
        title: "Dental Implants",
        description: "Restore missing teeth with permanent, natural-looking implants. The gold standard for tooth replacement.",
        icon: Hammer,
        href: "/services/implants",
        color: "text-orange-500",
        bg: "bg-orange-500/10",
    },
    {
        title: "General Checkups",
        description: "Preventive care to keep your teeth and gums healthy. Regular cleanings, exams, and x-rays.",
        icon: Stethoscope,
        href: "/services/general",
        color: "text-green-500",
        bg: "bg-green-500/10",
    },
    {
        title: "Pediatric Dentistry",
        description: "Gentle care for your little ones. We make visiting the dentist fun and educational for children.",
        icon: Smile, // Reusing Smile for now
        href: "/services/pediatric",
        color: "text-pink-500",
        bg: "bg-pink-500/10",
    },
    {
        title: "Emergency Care",
        description: "Immediate attention for toothaches, broken teeth, and other dental emergencies. We are here when you need us.",
        icon: Stethoscope, // Reusing Stethoscope
        href: "/services/emergency",
        color: "text-red-500",
        bg: "bg-red-500/10",
    },
]

export default function ServicesPage() {
    return (
        <main className="flex min-h-screen flex-col pt-24 pb-20">
            <div className="container px-8 sm:px-4 md:px-12 space-y-12">
                {/* Header */}
                <div className="text-center max-w-3xl mx-auto space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <h1 className="text-4xl md:text-6xl font-bold tracking-tighter">Our Services</h1>
                    <p className="text-xl text-muted-foreground">
                        Comprehensive dental care tailored to your unique needs. From routine checkups to complex makeovers, we have you covered.
                    </p>
                </div>

                {/* Services Grid */}
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {services.map((service, index) => (
                        <Link
                            key={service.title}
                            href={service.href}
                            className="group relative overflow-hidden rounded-3xl border bg-background p-8 transition-all hover:shadow-2xl hover:-translate-y-1 hover:border-[#25D366]/50"
                        >
                            <div className={`mb-6 inline-flex h-14 w-14 items-center justify-center rounded-2xl ${service.bg} ${service.color}`}>
                                <service.icon className="h-7 w-7" />
                            </div>
                            <h3 className="mb-3 text-2xl font-bold tracking-tight">{service.title}</h3>
                            <p className="mb-6 text-muted-foreground leading-relaxed">
                                {service.description}
                            </p>
                            <div className="flex items-center text-sm font-medium text-[#25D366] opacity-0 transition-opacity group-hover:opacity-100">
                                Learn more <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                            </div>
                        </Link>
                    ))}
                </div>
            </div>

            {/* Final CTA */}
            <CTABanner />
        </main>
    )
}
