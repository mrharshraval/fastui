import { SectionHeading } from "./section-heading";

export function ServicesList() {
  const services = [
    {
      title: "Strategy",
      description: "Digital strategy, positioning and product direction.",
    },
    {
      title: "Brand Identity",
      description: "Visual identity systems designed for modern businesses.",
    },
    {
      title: "UI/UX Design",
      description: "Interfaces that are clear, intuitive and purposeful.",
    },
    {
      title: "Web Design",
      description: "High-quality websites designed around business goals.",
    },
    {
      title: "Web Development",
      description: "Fast, responsive and scalable websites using modern web technologies.",
    },
    {
      title: "E-commerce",
      description: "Conversion-focused online stores and digital commerce experiences.",
    },
  ];

  return (
    <section className="py-24 px-8 md:px-16 lg:px-20 bg-secondary/30">
      <div className="container max-w-7xl mx-auto">
        <SectionHeading subtitle="What we do">Our Services</SectionHeading>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-12 gap-y-16">
          {services.map((service, index) => (
            <div key={index} className="group pt-6">
              <div className="text-muted-foreground text-sm font-medium mb-4">
                0{index + 1}
              </div>
              <h3 className="text-xl font-medium mb-3 group-hover:text-foreground/80 transition-colors">
                {service.title}
              </h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                {service.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
