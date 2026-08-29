"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";
import Link from "next/link";

export function CookieConsent() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Check if consent has already been given
    const consent = localStorage.getItem("cookie-consent");
    if (!consent) {
      setIsVisible(true);
    }
  }, []);

  if (!isVisible) return null;

  const acceptCookies = () => {
    localStorage.setItem("cookie-consent", "accepted");
    setIsVisible(false);
  };

  const rejectCookies = () => {
    localStorage.setItem("cookie-consent", "rejected");
    setIsVisible(false);
  };

  return (
    <div className="fixed bottom-4 right-4 md:bottom-8 md:right-8 z-50 max-w-[600px] w-[calc(100vw-32px)] bg-background border border-border rounded-2xl p-6 md:p-8 animate-in slide-in-from-bottom-8 fade-in duration-700">
      <button 
        onClick={() => setIsVisible(false)}
        className="absolute top-6 right-6 text-muted-foreground hover:text-foreground transition-colors"
        aria-label="Close"
      >
        <X className="w-5 h-5 stroke-[2.5]" />
      </button>

      <p className="text-[15px] leading-relaxed text-foreground pr-8 mb-8">
        We use cookies to make your interactions with our website more meaningful. They help us better understand how our websites are used, so we can tailor content for you. For more information about the different cookies we are using, read the <Link href="#" className="text-primary border border-primary px-1 hover:bg-primary/10 transition-colors">Cookie Policy</Link>. To change your cookie settings and preferences, click the Customize Cookies button.
      </p>

      <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
        <button className="text-sm font-semibold underline underline-offset-4 hover:text-primary transition-colors">
          Customize Cookies
        </button>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Button onClick={rejectCookies} className="rounded-full px-8 h-10 text-[15px] font-semibold flex-1 sm:flex-none">
            Reject
          </Button>
          <Button onClick={acceptCookies} className="rounded-full px-8 h-10 text-[15px] font-semibold flex-1 sm:flex-none">
            Accept
          </Button>
        </div>
      </div>
    </div>
  );
}
