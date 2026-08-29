import { Navigation } from "@/components/navigation";
import { Footer } from "@/components/footer";
import { CTA } from "@/components/cta";
import { SectionHeading } from "@/components/section-heading";

export const metadata = {
  title: "About | FastUI",
  description: "About FastUI. Our beliefs, approach, and capabilities.",
};

export default function AboutPage() {
  return (
    <>
      <Navigation />
      <main className="min-h-screen pt-32">
        
        {/* Header */}
        <section className="py-24 px-8 md:px-16 lg:px-20">
          <div className="container max-w-7xl mx-auto">
            <div className="max-w-4xl space-y-6">
              <h1 className="text-5xl md:text-7xl font-medium tracking-tight">
                Design-led. <br /> Technology-driven.
              </h1>
              <p className="text-xl text-muted-foreground max-w-2xl leading-relaxed">
                FastUI is a digital agency built for modern businesses. We combine strategic thinking with premium design to create digital experiences that perform.
              </p>
            </div>
          </div>
        </section>

        {/* Feature Image Placeholder */}
        <section className="px-8 md:px-16 lg:px-20 py-12">
          <div className="container max-w-7xl mx-auto">
            <div className="w-full aspect-video bg-muted rounded-md flex items-center justify-center text-muted-foreground">
              Studio Image Placeholder
            </div>
          </div>
        </section>

        {/* What We Believe */}
        <section className="py-24 px-8 md:px-16 lg:px-20 border-t border-border">
          <div className="container max-w-7xl mx-auto flex flex-col md:flex-row gap-12 md:gap-24">
            <div className="md:w-1/3">
              <h2 className="text-3xl font-medium tracking-tight">What we believe</h2>
            </div>
            <div className="md:w-2/3 max-w-2xl space-y-8 text-lg text-muted-foreground leading-relaxed">
              <p>
                We believe that the best digital experiences are invisible. They don't draw attention to how they were built, but rather to what they allow the user to accomplish.
              </p>
              <p>
                In a crowded market, generic templates and off-the-shelf solutions are no longer enough. Brands need intentional, custom-designed platforms that reflect their specific values and meet their unique business goals.
              </p>
              <p>
                That's why we focus on fundamental principles: clean typography, purposeful whitespace, intuitive navigation, and flawless technical execution.
              </p>
            </div>
          </div>
        </section>

        {/* Our Approach */}
        <section className="py-24 px-8 md:px-16 lg:px-20 border-t border-border bg-secondary/30">
          <div className="container max-w-7xl mx-auto flex flex-col md:flex-row gap-12 md:gap-24">
            <div className="md:w-1/3">
              <h2 className="text-3xl font-medium tracking-tight">Our approach</h2>
            </div>
            <div className="md:w-2/3 max-w-2xl space-y-12">
              
              <div className="space-y-4">
                <h3 className="text-xl font-medium text-foreground">Business-first</h3>
                <p className="text-muted-foreground leading-relaxed">
                  Every decision we make is rooted in your commercial objectives. We don't design for the sake of design; we design to solve problems and drive growth.
                </p>
              </div>

              <div className="space-y-4">
                <h3 className="text-xl font-medium text-foreground">Highly collaborative</h3>
                <p className="text-muted-foreground leading-relaxed">
                  We work closely with our clients, treating them as partners rather than just customers. Transparency and clear communication are at the core of our process.
                </p>
              </div>

              <div className="space-y-4">
                <h3 className="text-xl font-medium text-foreground">Uncompromising quality</h3>
                <p className="text-muted-foreground leading-relaxed">
                  From the initial strategy phase to the final line of code, we maintain an obsessive attention to detail. We build things right the first time.
                </p>
              </div>

            </div>
          </div>
        </section>

        <CTA />
      </main>
      <Footer />
    </>
  );
}
