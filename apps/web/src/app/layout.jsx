import "./globals.css";

export const metadata = {
  title: "FastUI — Digital Experiences for Modern Businesses",
  description: "FastUI builds high-quality digital experiences for modern businesses.",
};

import { Preloader } from "@/components/preloader";
import { CookieConsent } from "@/components/cookie-consent";

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`font-sans h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans">
        <Preloader />
        <CookieConsent />
        {children}
      </body>
    </html>
  );
}
