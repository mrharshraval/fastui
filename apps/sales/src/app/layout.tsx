import type { Metadata } from "next"
import localFont from "next/font/local"
import { Geist_Mono } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { TooltipProvider } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

const polymath = localFont({
  src: "../../public/font/Polymath/PolymathVar.woff2",
  variable: "--font-sans",
})

const fontMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
})

export const metadata: Metadata = {
  title: {
    default: "fastui sales",
    template: "%s | fastui sales",
  },
  description: "Sales CRM & Prospecting Platform",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "FastUI Sales",
  },
  icons: {
    icon: [
      { url: "/assets/brand/favicon/brand/primary/filled.svg", type: "image/svg+xml" },
      { url: "/assets/brand/favicon/brand/primary/filled.png", type: "image/png", sizes: "512x512" },
    ],
    shortcut: "/assets/brand/favicon/brand/primary/filled.png",
    apple: "/assets/brand/favicon/brand/primary/filled.png",
  },
}


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn("dark antialiased", fontMono.variable, "font-sans", polymath.variable)}
    >
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var s=localStorage.getItem("theme")||"dark";var r=s==="system"?(window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"):s;var d=document.documentElement;d.classList.remove("light","dark");d.classList.add(r);d.style.colorScheme=r;}catch(e){}})();
            if ('serviceWorker' in navigator) { window.addEventListener('load', function() { navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(function(){}); }); }`,
          }}
        />
      </head>

      <body>
        <ThemeProvider>
          <TooltipProvider delayDuration={300}>
            {children}
          </TooltipProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
