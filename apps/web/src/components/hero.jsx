"use client";

import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function Hero() {
  return (
    <section className="relative min-h-[100vh] flex flex-col justify-start md:justify-center pt-32 pb-16 md:pt-0 md:pb-0 px-8 md:px-16 lg:px-20 overflow-hidden bg-background" id="hero-root">

      {/* Content Overlay */}
      <div className="relative z-10 w-full max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between text-left animate-in fade-in slide-in-from-bottom-8 duration-1000 ease-out pt-12 md:pt-20 gap-8 md:gap-12">

        {/* Text Content */}
        <div className="pointer-events-auto flex flex-col items-start text-left space-y-4 w-full max-w-2xl">

          <h1 className="text-4xl md:text-6xl lg:text-7xl font-heading font-bold tracking-tight leading-tight text-left text-black">
            Get online faster
          </h1>

          <p className="text-xl md:text-3xl text-black font-medium max-w-2xl text-left">
            Everything your small business needs to get online. Websites, software, marketing, and more.
          </p>

          {/* Desktop CTA */}
          <div className="hidden md:flex flex-col sm:flex-row gap-4 justify-start pt-6 md:pt-8 w-full">
            <Link href="/contact" className={cn(buttonVariants({ size: "default" }), "h-14 px-10 text-lg rounded-full transition-all")}>
              Get in touch
            </Link>
          </div>
        </div>

        {/* Video Graphic */}
        <div className="pointer-events-none w-full max-w-xl flex justify-center md:justify-end mb-4 md:mb-0">
          <video
            src="/assets/hero-graphics.mp4"
            autoPlay
            loop
            muted
            playsInline
            className="w-full h-auto max-w-[500px] object-contain [clip-path:inset(2px)]"
          />
        </div>

        {/* Mobile CTA */}
        <div className="md:hidden flex flex-col sm:flex-row gap-4 justify-start w-full">
          <Link href="/contact" className={cn(buttonVariants({ size: "default" }), "h-14 px-10 text-lg rounded-full transition-all w-full flex items-center justify-center")}>
            Get in touch
          </Link>
        </div>
      </div>
    </section>
  );
}
