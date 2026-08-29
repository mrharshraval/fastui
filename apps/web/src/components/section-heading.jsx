export function SectionHeading({ children, subtitle, className = "" }) {
  return (
    <div className={`mb-16 md:mb-24 flex flex-col md:flex-row md:items-end justify-between gap-6 ${className}`}>
      <h2 className="text-4xl md:text-5xl font-medium tracking-tight max-w-2xl">
        {children}
      </h2>
      {subtitle && (
        <p className="text-muted-foreground text-sm md:text-base max-w-xs md:text-right">
          {subtitle}
        </p>
      )}
    </div>
  );
}
