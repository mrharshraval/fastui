"use client"

import { Button } from "@/components/ui/button"
import { CheckCircle2, CreditCard, FileText, ShieldCheck } from "lucide-react"
import { CTABanner } from "@/components/sections/cta-banner"

export default function Insurance() {
    return (
        <main className="flex flex-col min-h-screen bg-background">
            {/* Hero Section */}
            <section className="w-full py-24 bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="flex flex-col items-center text-center md:items-start md:text-left gap-6 max-w-3xl mx-auto md:mx-0">
                        <div className="inline-flex items-center rounded-full border bg-background px-3 py-1 text-sm font-medium text-muted-foreground border-border w-fit">
                            Insurance & Financing
                        </div>
                        <h1 className="text-4xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none text-foreground text-center md:text-left">
                            Quality care that fits your budget.
                        </h1>
                        <p className="text-lg text-muted-foreground leading-relaxed max-w-2xl text-center md:text-left">
                            We believe everyone deserves a healthy smile. We accept most major insurance plans and offer flexible financing options.
                        </p>
                    </div>
                </div>
            </section>

            {/* Insurance Section */}
            <section className="w-full py-24 bg-background">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="grid gap-12 lg:grid-cols-2">
                        <div className="space-y-8 text-center md:text-left">
                            <div className="flex items-center justify-center md:justify-start gap-4">
                                <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                                    <ShieldCheck className="h-6 w-6" />
                                </div>
                                <h2 className="text-3xl font-bold tracking-tighter">Dental Insurance</h2>
                            </div>
                            <p className="text-muted-foreground text-lg">
                                We are in-network with many major PPO dental insurance providers. Our team will handle all the paperwork and help you maximize your benefits.
                            </p>
                            <div className="grid grid-cols-2 gap-4 justify-items-center md:justify-items-start">
                                {[
                                    "Delta Dental", "Cigna", "Aetna", "MetLife",
                                    "Guardian", "United Healthcare", "Blue Cross Blue Shield", "Humana"
                                ].map((provider, i) => (
                                    <div key={i} className="flex items-center gap-2 text-sm font-medium">
                                        <CheckCircle2 className="h-4 w-4 text-primary" />
                                        {provider}
                                    </div>
                                ))}
                            </div>
                            <p className="text-sm text-muted-foreground italic">
                                *Don't see your plan? Call us to check coverage.
                            </p>
                        </div>
                        <div className="bg-secondary/30 p-8 rounded-xl">
                            <h3 className="font-bold text-xl mb-4">No Insurance? No Problem.</h3>
                            <p className="text-muted-foreground mb-6">
                                Join our **In-House Membership Plan** for an affordable annual fee.
                            </p>
                            <ul className="space-y-4 mb-8">
                                <li className="flex items-start gap-3">
                                    <CheckCircle2 className="h-5 w-5 text-primary mt-0.5" />
                                    <span>2 Professional Cleanings per year</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <CheckCircle2 className="h-5 w-5 text-primary mt-0.5" />
                                    <span>Unlimited Exams & X-Rays</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <CheckCircle2 className="h-5 w-5 text-primary mt-0.5" />
                                    <span>15-20% Off All Other Treatments</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <CheckCircle2 className="h-5 w-5 text-primary mt-0.5" />
                                    <span>No waiting periods or deductibles</span>
                                </li>
                            </ul>
                            <Button className="w-full rounded-full">Learn More About Membership</Button>
                        </div>
                    </div>
                </div>
            </section>

            {/* Financing Section */}
            <section className="w-full py-24 bg-muted md:bg-muted/30">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="flex flex-col items-center text-center space-y-8 max-w-3xl mx-auto">
                        <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                            <CreditCard className="h-6 w-6" />
                        </div>
                        <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">Flexible Financing Options</h2>
                        <p className="text-lg text-muted-foreground">
                            We partner with third-party lenders to offer payment plans that allow you to pay for your treatment over time, often with 0% interest.
                        </p>
                        <div className="grid gap-6 sm:grid-cols-2 w-full pt-8">
                            <div className="bg-background p-6 rounded-xl shadow-sm border border-border/50">
                                <h3 className="font-bold text-xl mb-2">CareCredit</h3>
                                <p className="text-sm text-muted-foreground mb-4">
                                    The nation's leading patient financing program.
                                </p>
                                <Button variant="outline" size="sm" className="rounded-full">Apply Now</Button>
                            </div>
                            <div className="bg-background p-6 rounded-xl shadow-sm border border-border/50">
                                <h3 className="font-bold text-xl mb-2">LendingClub</h3>
                                <p className="text-sm text-muted-foreground mb-4">
                                    Simple, transparent monthly payment options.
                                </p>
                                <Button variant="outline" size="sm" className="rounded-full">Apply Now</Button>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Payment Methods */}
            <section className="w-full py-24 bg-background">
                <div className="container px-8 sm:px-4 md:px-12">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-8 p-8 rounded-xl bg-secondary/30">
                        <div className="flex items-center gap-4">
                            <div className="h-10 w-10 rounded-full bg-background flex items-center justify-center">
                                <FileText className="h-5 w-5" />
                            </div>
                            <div>
                                <h3 className="font-bold text-lg">Payment Methods</h3>
                                <p className="text-sm text-muted-foreground">We accept cash, checks, and all major credit cards.</p>
                            </div>
                        </div>
                        <div className="flex gap-4 opacity-70 grayscale hover:grayscale-0 transition-all">
                            {/* Icons for Visa, Mastercard, Amex, Discover would go here */}
                            <span className="font-bold text-xl">VISA</span>
                            <span className="font-bold text-xl">Mastercard</span>
                            <span className="font-bold text-xl">AMEX</span>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA */}
            <CTABanner />
        </main>
    )
}
