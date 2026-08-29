import Link from "next/link";
import { Hexagon } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-background px-8 md:px-16 lg:px-20 py-16 md:py-24">
      <div className="container max-w-7xl mx-auto flex flex-col md:flex-row md:justify-between gap-12 md:gap-8">
        
        {/* Columns Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-12 md:gap-24 w-full">
          
          <div className="space-y-6">
            <h4 className="text-sm font-semibold tracking-tight text-foreground">Platform</h4>
            <nav className="flex flex-col gap-4 text-sm font-medium text-muted-foreground">
              <Link href="/services" className="hover:text-foreground transition-colors">Services</Link>
              <Link href="/about" className="hover:text-foreground transition-colors">About Us</Link>
            </nav>
          </div>

          <div className="space-y-6">
            <h4 className="text-sm font-semibold tracking-tight text-foreground">Information</h4>
            <nav className="flex flex-col gap-4 text-sm font-medium text-muted-foreground">
              <Link href="#" className="hover:text-foreground transition-colors">About us</Link>
              <Link href="#" className="hover:text-foreground transition-colors">Safety Center</Link>
              <Link href="#" className="hover:text-foreground transition-colors">Community Guidelines</Link>
              <Link href="#" className="hover:text-foreground transition-colors">Help Center / FAQs</Link>
            </nav>
          </div>
          
          <div className="space-y-6">
            <h4 className="text-sm font-semibold tracking-tight text-foreground">Legal</h4>
            <nav className="flex flex-col gap-4 text-sm font-medium text-muted-foreground">
              <Link href="#" className="hover:text-foreground transition-colors">Terms of Use</Link>
              <Link href="#" className="hover:text-foreground transition-colors">Privacy Policy</Link>
              <Link href="#" className="hover:text-foreground transition-colors">Cookie Policy</Link>
              <Link href="#" className="hover:text-foreground transition-colors">Acceptable Use</Link>
              <Link href="#" className="hover:text-foreground transition-colors">Content Moderation</Link>
              <Link href="#" className="hover:text-foreground transition-colors">Copyright Policy</Link>
              <Link href="#" className="hover:text-foreground transition-colors">Legal Requests</Link>
            </nav>
          </div>

          <div className="space-y-6">
            <h4 className="text-sm font-semibold tracking-tight text-foreground">Connect</h4>
            <nav className="flex flex-col gap-4 text-sm font-medium text-muted-foreground">
              <Link href="/contact" className="hover:text-foreground transition-colors">Contact Support</Link>
            </nav>
          </div>

        </div>
      </div>
      
      {/* Bottom Section - Huge Logo */}
      <div className="container max-w-7xl mx-auto mt-16 md:mt-32">
        <div className="w-full pt-8 pb-8">
          <img 
            src="/brand/wordmark/monochrome/black%20filled.svg" 
            alt="FastUI Logo" 
            className="w-full h-auto object-contain dark:invert"
          />
        </div>
        <div className="flex flex-col sm:flex-row justify-between items-center gap-6 text-sm font-medium text-muted-foreground pb-8 pt-8">
          <p>© 2026 FastUI. All rights reserved.</p>
          <p>Digital experiences for modern businesses.</p>
        </div>
      </div>
    </footer>
  );
}
