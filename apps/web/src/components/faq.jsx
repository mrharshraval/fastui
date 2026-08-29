import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export function FAQ() {
  const faqs = [
    {
      question: "What is your typical project timeline?",
      answer: "Most of our web design and development projects take between 8 to 12 weeks from initial discovery to final launch. More complex platforms or e-commerce builds may take 16+ weeks. We establish a clear timeline during the discovery phase.",
    },
    {
      question: "Do you work with startups or established enterprises?",
      answer: "Both. We partner with ambitious startups looking to establish a premium digital presence, as well as established enterprises seeking to modernize their platforms and improve conversion rates.",
    },
    {
      question: "What technologies do you use?",
      answer: "We specialize in modern web technologies that prioritize performance and scalability. Our primary stack includes React, Next.js, and Tailwind CSS. For content management, we often implement headless CMS solutions like Sanity or Contentful.",
    },
    {
      question: "Can you help with brand identity as well?",
      answer: "Yes. While our primary focus is digital, we often develop comprehensive brand identities alongside web projects to ensure a cohesive and impactful presence across all touchpoints.",
    },
    {
      question: "How much does a typical project cost?",
      answer: "Our project minimum is generally $15,000 for a comprehensive website redesign. Final costs depend heavily on the scope, technical complexity, and timeline of the project. We provide detailed, transparent quotes after our initial consultation.",
    },
  ];

  return (
    <section className="py-24 px-8 md:px-16 lg:px-20">
      <div className="container max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row gap-12 md:gap-24">
          <div className="md:w-1/3 space-y-4">
            <p className="text-muted-foreground text-sm font-medium tracking-widest uppercase">
              Got questions?
            </p>
            <h2 className="text-4xl md:text-5xl font-medium tracking-tight">
              Frequently <br className="hidden md:block" />Asked Questions
            </h2>
          </div>
          <div className="md:w-2/3 max-w-3xl">
            <Accordion type="single" className="w-full">
              {faqs.map((faq, index) => (
                <AccordionItem key={index} value={`item-${index}`}>
                  <AccordionTrigger className="text-left text-lg font-medium py-6 hover:no-underline hover:text-muted-foreground transition-colors">
                    {faq.question}
                  </AccordionTrigger>
                  <AccordionContent className="text-muted-foreground text-base leading-relaxed pb-6">
                    {faq.answer}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        </div>
      </div>
    </section>
  );
}
