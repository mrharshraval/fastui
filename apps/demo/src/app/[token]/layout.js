import { notFound } from "next/navigation"
import { Navbar } from "@/components/layout/navbar"
import { Footer } from "@/components/layout/footer"
import { DemoProvider } from "@/lib/demo-context"
import { getDemoData } from "@/lib/demo-api"
import { FloatingWhatsApp } from "@/components/floating-whatsapp"
import { DemoAnalytics } from "@/components/demo-analytics"

export async function generateMetadata({ params }) {
  const resolvedParams = await params
  const token = resolvedParams?.token
  const demoData = await getDemoData(token)

  if (!demoData) {
    return {
      title: "Not Found",
      robots: { index: false, follow: false },
    }
  }

  const clinicName = demoData?.business?.name || "Dental Studio"
  const city = demoData?.business?.city ? ` in ${demoData.business.city}` : ""

  const title = `${clinicName} — Website Preview`
  const description = `Personalized website preview for ${clinicName}${city}. Includes seamless online booking, dental treatments overview, and patient-first modern design.`

  return {
    title,
    description,
    robots: {
      index: false,
      follow: false,
    },
    openGraph: {
      title,
      description,
      type: "website",
      url: `https://demo.fastui.in/${token}`,
      siteName: clinicName,
      images: [
        {
          url: "/hero_dentist_v1.webp",
          width: 1200,
          height: 630,
          alt: `${clinicName} Website Preview`,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: ["/hero_dentist_v1.webp"],
    },
  }
}

export default async function TokenLayout({ children, params }) {
  const resolvedParams = await params
  const token = resolvedParams?.token
  const demoData = await getDemoData(token)

  if (!demoData) {
    notFound()
  }

  return (
    <DemoProvider token={token} demoData={demoData}>
      <div className="flex min-h-screen flex-col">
        <Navbar />
        <main className="flex-1">{children}</main>
        <FloatingWhatsApp />
        <Footer />
        <DemoAnalytics token={token} />
      </div>
    </DemoProvider>
  )
}
