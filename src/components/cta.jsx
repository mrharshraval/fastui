import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function CTA() {
  return (
    <section className="relative min-h-[90vh] flex flex-col justify-center items-center py-32 px-8 md:px-16 lg:px-20 overflow-hidden bg-background">
      {/* Content Overlay */}
      <div className="relative z-10 container max-w-4xl mx-auto flex flex-col items-center text-center gap-8">
        <div className="space-y-6">
          <h2 className="text-[clamp(2.5rem,8vw,4rem)] font-bold text-foreground leading-[1.2] tracking-tight">
            Design that drives results.
          </h2>
          <p className="text-[clamp(1rem,2.5vw,1.25rem)] text-[#666666] font-normal leading-[1.6] max-w-2xl mx-auto">
            We partner with SaaS founders to build experiences that convert.
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4 w-full sm:w-auto">
          <Link href="/contact" className={cn(buttonVariants({ size: "default" }), "w-full sm:w-auto h-14 px-10 text-lg rounded-[50px] bg-foreground text-background hover:bg-foreground/90 transition-all shadow-none")}>
            Start Your Project
          </Link>
          <Link href="/work" className={cn(buttonVariants({ variant: "outline", size: "default" }), "w-full sm:w-auto h-14 px-10 text-lg rounded-[50px] bg-transparent border-[#e0e0e0] text-foreground hover:bg-[#f5f5f5] hover:text-black transition-all shadow-none")}>
            View Our Work
          </Link>
        </div>
      </div>
    </section>
  );
}
