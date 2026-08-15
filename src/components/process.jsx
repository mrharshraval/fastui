
export function Process() {
  const steps = [
    {
      title: "Discover",
      description: "Understand the business, audience and problem.",
    },
    {
      title: "Define",
      description: "Establish strategy, structure and direction.",
    },
    {
      title: "Design",
      description: "Create the visual and user experience.",
    },
    {
      title: "Build",
      description: "Develop the website using modern web technology.",
    },
    {
      title: "Launch",
      description: "Test, refine and launch the final experience.",
    },
  ];

  return (
    <section id="process" className="py-24 px-8 md:px-16 lg:px-20">
      <div className="container max-w-7xl mx-auto">
        <div className="max-w-4xl mb-16 md:mb-24 space-y-4">
          <p className="text-muted-foreground text-sm font-medium tracking-widest uppercase">
            How we work
          </p>
          <h2 className="text-3xl md:text-5xl font-medium tracking-tight">
            Our Process
          </h2>
        </div>
        
        <div className="max-w-4xl space-y-12">
          {steps.map((step, index) => (
            <div key={index} className="flex flex-col md:flex-row md:items-baseline gap-4 md:gap-16 pb-12 last:pb-0">
              <div className="text-xl font-medium min-w-[200px]">
                <span className="text-muted-foreground mr-4 text-sm font-normal">
                  0{index + 1} —
                </span>
                {step.title}
              </div>
              <p className="text-muted-foreground text-lg">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
