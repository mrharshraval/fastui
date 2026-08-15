import { notFound } from "next/navigation";
import { Navigation } from "@/components/navigation";
import { Footer } from "@/components/footer";
import { CTA } from "@/components/cta";
import { projects } from "@/lib/project-data";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

export function generateMetadata({ params }) {
  const project = projects.find((p) => p.slug === params.slug);
  if (!project) return { title: "Project Not Found" };
  
  return {
    title: `${project.title} | FastUI`,
    description: project.description,
  };
}

export default function CaseStudyPage({ params }) {
  const project = projects.find((p) => p.slug === params.slug);
  
  if (!project) {
    notFound();
  }

  return (
    <>
      <Navigation />
      <main className="min-h-screen pt-32">
        {/* Project Header */}
        <header className="py-16 md:py-24 px-8 md:px-16 lg:px-20 border-b border-border">
          <div className="container max-w-7xl mx-auto">
            <h1 className="text-5xl md:text-7xl font-medium tracking-tight max-w-4xl mb-16">
              {project.title}
            </h1>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-sm border-t border-border pt-8">
              <div>
                <h4 className="text-muted-foreground mb-2">Client</h4>
                <p className="font-medium">{project.client}</p>
              </div>
              <div>
                <h4 className="text-muted-foreground mb-2">Industry</h4>
                <p className="font-medium">{project.category}</p>
              </div>
              <div>
                <h4 className="text-muted-foreground mb-2">Services</h4>
                <div className="flex flex-col gap-1 font-medium">
                  {project.services.map(s => <span key={s}>{s}</span>)}
                </div>
              </div>
              <div>
                <h4 className="text-muted-foreground mb-2">Year</h4>
                <p className="font-medium">{project.year}</p>
              </div>
              {project.metric && (
                <div>
                  <h4 className="text-muted-foreground mb-2">Key Metric</h4>
                  <p className="font-medium text-primary">{project.metric}</p>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Hero Image */}
        <section className="px-8 md:px-16 lg:px-20 py-12">
          <div className="container max-w-7xl mx-auto">
            <div className="w-full aspect-[21/9] bg-muted rounded-md overflow-hidden flex items-center justify-center text-muted-foreground text-lg">
              {project.image ? (
                <img src={project.image} alt={project.title} className="w-full h-full object-cover" />
              ) : (
                "Primary Case Study Image Placeholder"
              )}
            </div>
          </div>
        </section>

        {/* Project Content */}
        <article className="py-24 px-8 md:px-16 lg:px-20 container max-w-7xl mx-auto space-y-24">
          
          <section className="space-y-6">
            <h2 className="text-3xl font-medium">The Challenge</h2>
            <p className="text-xl text-muted-foreground leading-relaxed">
              [Placeholder text] The existing platform was struggling with outdated design patterns and poor performance, leading to high bounce rates and low engagement. The challenge was to rebuild the experience from the ground up without alienating their core user base.
            </p>
          </section>

          <section className="space-y-6 border-t border-border pt-12">
            <h2 className="text-3xl font-medium">Our Approach</h2>
            <p className="text-lg text-muted-foreground leading-relaxed">
              [Placeholder text] We began with a comprehensive audit of the existing user journeys, identifying key friction points. By streamlining the navigation and adopting a modular design system, we were able to create a more intuitive flow.
            </p>
          </section>
          
          <section className="space-y-6 border-t border-border pt-12">
            <h2 className="text-3xl font-medium">The Solution</h2>
            <p className="text-lg text-muted-foreground leading-relaxed">
              [Placeholder text] The visual language was refined to communicate trust and authority. On the technical side, we migrated the platform to a modern Next.js stack, significantly improving load times and SEO performance.
            </p>
          </section>

          <section className="space-y-6 border-t border-border pt-12">
            <h2 className="text-3xl font-medium">Results & Metrics</h2>
            <p className="text-lg text-muted-foreground leading-relaxed">
              [Placeholder text] The new platform launched to overwhelmingly positive feedback, directly achieving the business goals set out in the strategy phase.
            </p>
            {project.metric && (
              <div className="mt-8 p-8 bg-secondary/30 rounded-lg border border-border inline-block">
                <p className="text-4xl font-medium text-primary tracking-tight mb-2">{project.metric}</p>
                <p className="text-sm text-muted-foreground uppercase tracking-widest font-medium">Key Outcome</p>
              </div>
            )}
          </section>

        </article>

        {/* More Projects */}
        <section className="py-24 px-8 md:px-16 lg:px-20 border-t border-border bg-secondary/30">
          <div className="container max-w-7xl mx-auto text-center">
            <h3 className="text-2xl font-medium mb-8">More Projects</h3>
            <Link 
              href="/work" 
              className="inline-flex items-center gap-2 text-lg font-medium hover:text-muted-foreground transition-colors"
            >
              Back to Portfolio <ArrowUpRight className="w-5 h-5" />
            </Link>
          </div>
        </section>

        <CTA />
      </main>
      <Footer />
    </>
  );
}
