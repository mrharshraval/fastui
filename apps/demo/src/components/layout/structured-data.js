import { siteConfig } from "@/config/site"

export function StructuredData() {
    const jsonLd = {
        "@context": "https://schema.org",
        "@type": "Dentist",
        "name": siteConfig.name,
        "image": siteConfig.ogImage,
        "description": siteConfig.description,
        "url": siteConfig.url,
        "telephone": siteConfig.phone,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": siteConfig.address.street,
            "addressLocality": siteConfig.address.city,
            "addressRegion": siteConfig.address.state,
            "postalCode": siteConfig.address.zip,
            "addressCountry": siteConfig.address.country,
        },
        "priceRange": "$$",
        "openingHoursSpecification": [
            {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday"
                ],
                "opens": "09:00",
                "closes": "18:00"
            }
        ],
        "sameAs": [
            siteConfig.links.twitter,
            siteConfig.links.github
        ]
    }

    return (
        <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
    )
}
