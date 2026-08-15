import { Hero } from "@/components/hero";
import { FAQ } from "@/components/faq";
import { CTA } from "@/components/cta";
import { SectionHeading } from "@/components/section-heading";
import { Navigation } from "@/components/navigation";
import { Footer } from "@/components/footer";
import { TrustedBy } from "@/components/trusted-by";
import { TrustedByLeaders } from "@/components/trusted-by-leaders";
import { FeatureCarousel } from "@/components/feature-carousel";

export default function Home() {
  return (
    <>
      <Navigation />
      <main className="min-h-screen">
        <Hero />
        <TrustedBy />
        <TrustedByLeaders />
        <FeatureCarousel />

        <FAQ />
        <CTA />
      </main>
      <Footer />
    </>
  );
}
