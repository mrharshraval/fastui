import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

export function ProjectCard({ project, number }) {
  return (
    <Link href={`/work/${project.slug}`} className="group block">
      <div className="flex flex-col gap-6">
        {/* Number and Meta Info */}
        <div className="flex justify-between items-end border-b border-border pb-4">
          <div className="text-sm font-medium text-muted-foreground flex gap-4">
            {number && <span>{number}</span>}
            <span>{project.client}</span>
          </div>
          <div className="text-right">
            <h3 className="text-2xl md:text-3xl font-medium tracking-tight group-hover:text-foreground/80 transition-colors">
              {project.title}
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              {project.services.join(" · ")}
            </p>
            {project.metric && (
              <p className="text-sm font-medium text-primary mt-3 inline-flex items-center px-3 py-1 bg-secondary/50 rounded-full border border-border/50">
                {project.metric}
              </p>
            )}
          </div>
        </div>
        
        {/* Image Container with subtle scale on hover */}
        <div className="relative aspect-[4/3] w-full overflow-hidden bg-muted rounded-md">
          {project.image ? (
            <img 
              src={project.image} 
              alt={project.title} 
              className="object-cover w-full h-full transition-transform duration-700 ease-out group-hover:scale-105"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-secondary/50 text-muted-foreground transition-transform duration-700 ease-out group-hover:scale-105">
              Image Placeholder
            </div>
          )}
          
          {/* Subtle overlay arrow that appears on hover */}
          <div className="absolute top-4 right-4 bg-background/90 backdrop-blur-sm p-3 rounded-full opacity-0 translate-y-2 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300">
            <ArrowUpRight className="w-5 h-5" />
          </div>
        </div>
      </div>
    </Link>
  );
}
