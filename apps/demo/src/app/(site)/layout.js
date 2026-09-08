import { Navbar } from "@/components/layout/navbar"
import { Footer } from "@/components/layout/footer"
import { StructuredData } from "@/components/layout/structured-data"
import { DemoProvider } from "@/lib/demo-context"
import { DEFAULT_DENTAL_DEMO } from "@/lib/demo-api"
import { FloatingWhatsApp } from "@/components/floating-whatsapp"

export default function SiteLayout({ children }) {
    return (
        <DemoProvider token="" demoData={DEFAULT_DENTAL_DEMO}>
            <div className="flex min-h-screen flex-col">
                <Navbar />
                <main className="flex-1">{children}</main>
                <Footer />
                <FloatingWhatsApp />
                <StructuredData />
            </div>
        </DemoProvider>
    )
}
