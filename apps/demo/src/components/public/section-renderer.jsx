"use client"

import { HeroModern } from "./sections/hero-modern"
import { RichTextSection } from "./sections/rich-text-section"
import { PublicCarouselSection } from "./sections/carousel-section"

// Content
import { PublicCodeSection } from "./sections/code-section"
import { PublicAlertSection } from "./sections/alert-section"
import { PublicDividerSection } from "./sections/divider-section"
import { PublicQuoteSection } from "./sections/quote-section"
import { PublicFAQSection } from "./sections/faq-section"

// Media
import { PublicGallerySection } from "./sections/gallery-section"
import { PublicVideoSection } from "./sections/video-section"
import { PublicAudioSection } from "./sections/audio-section"

// Marketing
import { PublicCTASection } from "./sections/cta-section"
import { PublicFeaturesSection } from "./sections/features-section"
import { PublicTestimonialSection } from "./sections/testimonial-section"
import { PublicStatsSection } from "./sections/stats-section"
import { PublicPricingSection } from "./sections/pricing-section"
import { PublicTeamSection } from "./sections/team-section"

// Utility
import { PublicNewsletterSection } from "./sections/newsletter-section"
import { PublicMapSection } from "./sections/map-section"
import { PublicTimelineSection } from "./sections/timeline-section"

const SECTIONS = {
    "hero-modern": HeroModern,
    "rich-text": RichTextSection,
    "carousel": PublicCarouselSection,

    // Content
    "code": PublicCodeSection,
    "alert": PublicAlertSection,
    "divider": PublicDividerSection,
    "quote": PublicQuoteSection,
    "faq": PublicFAQSection,

    // Media
    "gallery": PublicGallerySection,
    "video": PublicVideoSection,
    "audio": PublicAudioSection,

    // Marketing
    "cta": PublicCTASection,
    "features": PublicFeaturesSection,
    "testimonials": PublicTestimonialSection,
    "stats": PublicStatsSection,
    "pricing": PublicPricingSection,
    "team": PublicTeamSection,

    // Utility
    "newsletter": PublicNewsletterSection,
    "map": PublicMapSection,
    "timeline": PublicTimelineSection,
}

export function PublicSectionRenderer({ section }) {
    const Component = SECTIONS[section.type]

    if (!Component) {
        return null
    }

    return <Component data={section.data} />
}
