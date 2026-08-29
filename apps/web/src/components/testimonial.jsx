export function Testimonial() {
  return (
    <section className="py-32 px-8 md:px-16 lg:px-20 bg-secondary/50">
      <div className="container max-w-7xl mx-auto flex flex-col items-center text-center">
        <blockquote className="max-w-4xl space-y-8">
          <p className="text-3xl md:text-5xl font-medium tracking-tight leading-snug">
            "The new website completely changed how we present our business online."
          </p>
          <footer className="text-sm md:text-base text-muted-foreground font-medium uppercase tracking-widest">
            Client Name <span className="opacity-50 mx-2">·</span> Company
          </footer>
        </blockquote>
      </div>
    </section>
  );
}
