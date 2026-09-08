import { siteConfig } from "@/config/site"

export default function sitemap() {
    const routes = [
        "",
        "/about",
        "/contact",
        "/gallery",
        "/insurance",
        "/treatments",
        "/treatments/cosmetic",
        "/treatments/emergency",
        "/treatments/general",
        "/treatments/implants",
        "/treatments/invisalign",
        "/treatments/orthodontics",
        "/treatments/pediatric",
        "/treatments/surgical",
    ].map((route) => ({
        url: `${siteConfig.url}${route}`,
        lastModified: new Date(),
        changeFrequency: "monthly",
        priority: route === "" ? 1 : 0.8,
    }))

    return routes
}
