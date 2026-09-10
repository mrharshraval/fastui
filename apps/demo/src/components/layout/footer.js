"use client"

import * as React from "react"
import Link from "next/link"
import { siteConfig } from "@/config/site"
import { Icons } from "@/components/icons"
import { Facebook, Instagram, Twitter, Youtube, Mail, MapPin, Phone } from "lucide-react"
import { useDemo } from "@/lib/demo-context"

export function Footer() {
    const { business, customization, demoLink } = useDemo()
    const clinicName = business?.name || siteConfig.name
    const cityState = [business?.city, business?.state, business?.postal_code].filter(Boolean).join(", ")
    const socialLinks = customization?.social_links || business?.social_links || {}
    const whatsappUrl = customization?.whatsapp_url || (business?.whatsapp ? (business.whatsapp.startsWith("http") ? business.whatsapp : `https://wa.me/${business.whatsapp.replace(/\D/g, "")}`) : null)

    return (
        <footer className="bg-muted/30 border-t">
            <div className="container px-8 sm:px-4 md:px-12 py-12 md:py-16 lg:py-20">
                <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4 text-center md:text-left">
                    {/* Brand Section */}
                    <div className="space-y-4 flex flex-col items-center md:items-start">
                        <Link href={demoLink("/")} className="flex items-center space-x-2">
                            {business?.logo_url ? (
                                <img
                                    src={business.logo_url}
                                    alt={clinicName}
                                    className="h-7 max-w-[140px] object-contain"
                                    referrerPolicy="no-referrer"
                                />
                            ) : (
                                <>
                                    <Icons.logo className="h-6 w-6" />
                                    <span className="font-bold text-lg">{clinicName}</span>
                                </>
                            )}
                        </Link>
                        <p className="text-sm text-muted-foreground max-w-xs text-center md:text-left">
                            {customization?.tagline || "Providing advanced dental care with a focus on comfort and precision. Your smile is our priority."}
                        </p>
                        <div className="flex justify-center md:justify-start space-x-4">
                            {socialLinks.facebook ? (
                                <a href={socialLinks.facebook} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground transition-colors">
                                    <Facebook className="h-5 w-5" />
                                    <span className="sr-only">Facebook</span>
                                </a>
                            ) : (
                                <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
                                    <Facebook className="h-5 w-5" />
                                    <span className="sr-only">Facebook</span>
                                </Link>
                            )}
                            {socialLinks.instagram ? (
                                <a href={socialLinks.instagram} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground transition-colors">
                                    <Instagram className="h-5 w-5" />
                                    <span className="sr-only">Instagram</span>
                                </a>
                            ) : (
                                <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
                                    <Instagram className="h-5 w-5" />
                                    <span className="sr-only">Instagram</span>
                                </Link>
                            )}
                            {socialLinks.youtube && (
                                <a href={socialLinks.youtube} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground transition-colors">
                                    <Youtube className="h-5 w-5" />
                                    <span className="sr-only">YouTube</span>
                                </a>
                            )}
                            {socialLinks.twitter ? (
                                <a href={socialLinks.twitter} target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground transition-colors">
                                    <Twitter className="h-5 w-5" />
                                    <span className="sr-only">Twitter</span>
                                </a>
                            ) : (
                                <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
                                    <Twitter className="h-5 w-5" />
                                    <span className="sr-only">Twitter</span>
                                </Link>
                            )}
                        </div>
                    </div>

                    {/* Quick Links */}
                    <div className="space-y-4 flex flex-col items-center md:items-start">
                        <h3 className="font-semibold text-foreground">Quick Links</h3>
                        <ul className="space-y-2 text-sm text-center md:text-left">
                            <li>
                                <Link href={demoLink("/")} className="text-muted-foreground hover:text-foreground transition-colors">
                                    Home
                                </Link>
                            </li>
                            <li>
                                <Link href={demoLink("/about")} className="text-muted-foreground hover:text-foreground transition-colors">
                                    About Us
                                </Link>
                            </li>
                            <li>
                                <Link href={demoLink("/insurance")} className="text-muted-foreground hover:text-foreground transition-colors">
                                    Insurance
                                </Link>
                            </li>
                            <li>
                                <Link href={demoLink("/gallery")} className="text-muted-foreground hover:text-foreground transition-colors">
                                    Gallery
                                </Link>
                            </li>
                            <li>
                                <Link href={demoLink("/contact")} className="text-muted-foreground hover:text-foreground transition-colors">
                                    Contact
                                </Link>
                            </li>
                        </ul>
                    </div>

                    {/* Treatments */}
                    <div className="space-y-4 flex flex-col items-center md:items-start">
                        <h3 className="font-semibold text-foreground">Treatments</h3>
                        <ul className="space-y-2 text-sm text-center md:text-left">
                            <li>
                                <Link href={demoLink("/treatments/general")} className="text-muted-foreground hover:text-foreground transition-colors">
                                    General Checkups
                                </Link>
                            </li>
                            <li>
                                <Link href={demoLink("/treatments/cosmetic")} className="text-muted-foreground hover:text-foreground transition-colors">
                                    Cosmetic Dentistry
                                </Link>
                            </li>
                            <li>
                                <Link href={demoLink("/treatments/orthodontics")} className="text-muted-foreground hover:text-foreground transition-colors">
                                    Orthodontics
                                </Link>
                            </li>
                            <li>
                                <Link href={demoLink("/treatments/surgical")} className="text-muted-foreground hover:text-foreground transition-colors">
                                    Surgical Care
                                </Link>
                            </li>
                            <li>
                                <Link href={demoLink("/treatments/implants")} className="text-muted-foreground hover:text-foreground transition-colors">
                                    Dental Implants
                                </Link>
                            </li>
                            <li>
                                <Link href={demoLink("/treatments/pediatric")} className="text-muted-foreground hover:text-foreground transition-colors">
                                    Pediatric Dentistry
                                </Link>
                            </li>
                        </ul>
                    </div>

                    {/* Contact Info */}
                    <div className="space-y-4 flex flex-col items-center md:items-start">
                        <h3 className="font-semibold text-foreground">Contact</h3>
                        <ul className="space-y-3 text-sm text-center md:text-left flex flex-col items-center md:items-start">
                            <li className="flex items-start justify-center md:justify-start space-x-2 text-muted-foreground">
                                <MapPin className="h-4 w-4 mt-0.5 shrink-0" />
                                <span>
                                    {business?.address || "Medical Square"}<br />
                                    {cityState || "Ahmedabad, Gujarat"}
                                </span>
                            </li>
                            {business?.phone && (
                                <li className="flex items-center justify-center md:justify-start space-x-2 text-muted-foreground">
                                    <Phone className="h-4 w-4 shrink-0" />
                                    <a href={`tel:${business.phone}`} className="hover:text-foreground transition-colors">
                                        {business.phone}
                                    </a>
                                </li>
                            )}
                            {whatsappUrl && (
                                <li className="flex items-center justify-center md:justify-start space-x-2 text-muted-foreground">
                                    <Icons.whatsapp className="h-4 w-4 shrink-0" />
                                    <a
                                        href={whatsappUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="hover:text-foreground transition-colors"
                                    >
                                        {business?.whatsapp || business?.phone} (WhatsApp)
                                    </a>
                                </li>
                            )}
                            {business?.email && (
                                <li className="flex items-center justify-center md:justify-start space-x-2 text-muted-foreground">
                                    <Mail className="h-4 w-4 shrink-0" />
                                    <a href={`mailto:${business.email}`} className="hover:text-foreground transition-colors">
                                        {business.email}
                                    </a>
                                </li>
                            )}
                            {customization?.emergency_info && (
                                <li className="text-xs text-primary font-medium pt-1">
                                    {customization.emergency_info}
                                </li>
                            )}
                        </ul>
                    </div>
                </div>

                <div className="mt-12 pt-8 border-t text-center text-sm text-muted-foreground">
                    <p>&copy; {new Date().getFullYear()} {clinicName}. All rights reserved.</p>
                </div>
            </div>
        </footer>
    )
}
