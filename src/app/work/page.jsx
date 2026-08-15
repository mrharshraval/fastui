import { Navigation } from "@/components/navigation";
import { Footer } from "@/components/footer";
import { SectionHeading } from "@/components/section-heading";
import { ProjectCard } from "@/components/project-card";
import { CTA } from "@/components/cta";
import { projects } from "@/lib/project-data";

export const metadata = {
  title: "Work | FastUI",
  description: "View our selected portfolio of digital experiences and web platforms.",
};

export default function WorkPage() {
  return (
    <>
      <Navigation />
      <main className="min-h-screen pt-32">
        <section className="py-24 px-8 md:px-16 lg:px-20">
          <div className="container max-w-7xl mx-auto">
            <div className="max-w-4xl mb-24 space-y-6">
              <h1 className="text-5xl md:text-7xl font-medium tracking-tight">
                Selected Work
              </h1>
              <p className="text-xl text-muted-foreground max-w-2xl">
                A selection of digital platforms, marketing websites, and brands we've built for ambitious companies.
              </p>
            </div>

            <div className="space-y-24">
              {projects.map((project, index) => (
                <ProjectCard 
                  key={project.slug} 
                  project={project} 
                  number={`0${index + 1}`} 
                />
              ))}
            </div>
          </div>
        </section>
        
        <CTA />
      </main>
      <Footer />
    </>
  );
}
