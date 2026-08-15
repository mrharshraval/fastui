import { Navigation } from "@/components/navigation";
import { Footer } from "@/components/footer";
import { CTA } from "@/components/cta";

export const metadata = {
  title: "Services | FastUI",
  description: "Our digital capabilities, from strategy to development.",
};

export default function ServicesPage() {
  const services = [
    {
      title: "Strategy",
      description: "We help define clear digital roadmaps and product positioning that align with your commercial goals.",
      deliverables: ["Product Strategy", "Market Research", "Brand Positioning", "Digital Transformation"],
    },
    {
      title: "Brand Identity",
      description: "Visual identity systems designed for modern businesses that want to stand out and build trust.",
      deliverables: ["Logo Design", "Typography Systems", "Color Palettes", "Brand Guidelines"],
    },
    {
      title: "UI/UX Design",
      description: "Interfaces that are clear, intuitive and purposeful. We design for usability and conversion.",
      deliverables: ["UX Architecture", "Wireframing", "Interface Design", "Prototyping"],
    },
    {
      title: "Web Design",
      description: "High-quality, bespoke websites designed around your specific business objectives.",
      deliverables: ["Corporate Websites", "Marketing Sites", "Landing Pages", "Design Systems"],
    },
    {
      title: "Web Development",
      description: "Fast, responsive and scalable websites built on modern web technologies like Next.js and React.",
      deliverables: ["Front-end Development", "CMS Integration", "Performance Optimization", "Technical SEO"],
    },
    {
      title: "E-commerce",
      description: "Conversion-focused online stores and digital commerce experiences that scale.",
      deliverables: ["Shopify headless", "Custom Checkouts", "Inventory Integration", "Conversion Optimization"],
    },
  ];

  return (
    <>
      <Navigation />
      <main className="min-h-screen pt-32">
        
        {/* Header */}
        <section className="py-24 px-8 md:px-16 lg:px-20 border-b border-border">
          <div className="container max-w-7xl mx-auto">
            <div className="max-w-4xl space-y-6">
              <h1 className="text-5xl md:text-7xl font-medium tracking-tight">
                Our Capabilities
              </h1>
              <p className="text-xl text-muted-foreground max-w-2xl">
                We combine strategic thinking, premium design, and robust engineering to build digital experiences that perform.
              </p>
            </div>
          </div>
        </section>

        {/* Services List */}
        <section className="py-24 px-8 md:px-16 lg:px-20">
          <div className="container max-w-7xl mx-auto">
            <div className="max-w-5xl mx-auto space-y-24">
              {services.map((service, index) => (
                <div key={index} className="flex flex-col md:flex-row gap-8 md:gap-16">
                  
                  {/* Left Column: Number & Title */}
                  <div className="md:w-1/3 shrink-0">
                    <div className="text-muted-foreground mb-4 font-medium text-sm">
                      0{index + 1}
                    </div>
                    <h2 className="text-3xl font-medium tracking-tight">{service.title}</h2>
                  </div>

                  {/* Right Column: Description & Deliverables */}
                  <div className="md:w-2/3 space-y-8 md:pt-10">
                    <p className="text-xl text-muted-foreground leading-relaxed">
                      {service.description}
                    </p>
                    
                    <div className="space-y-4">
                      <h4 className="font-medium text-sm uppercase tracking-widest text-foreground/70">Includes</h4>
                      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-y-3 gap-x-8 text-muted-foreground">
                        {service.deliverables.map(item => (
                          <li key={item} className="flex items-center gap-3">
                            <span className="w-1.5 h-1.5 bg-border rounded-full"></span>
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                </div>
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
