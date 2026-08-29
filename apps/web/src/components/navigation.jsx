import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Menu } from "lucide-react";

export function Navigation() {
  const links = [
    { name: "Services", href: "/services" },
    { name: "Process", href: "/#process" },
    { name: "About", href: "/about" },
    { name: "Contact", href: "/contact" },
  ];

  return (
    <header className="fixed top-0 w-full z-50 bg-background/80 backdrop-blur-md px-8 md:px-16 lg:px-20">
      <div className="container max-w-7xl mx-auto h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center">
          <img 
            src="/brand/wordmark/monochrome/black%20filled.svg" 
            alt="FastUI" 
            className="h-8 w-auto dark:invert"
          />
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-12 text-sm font-medium">
          {links.map((link) => (
            <Link
              key={link.name}
              href={link.href}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              {link.name}
            </Link>
          ))}
        </nav>

        {/* Mobile Nav */}
        <div className="md:hidden">
          <Sheet>
            <SheetTrigger render={<Button variant="ghost" size="icon" aria-label="Menu" />}>
              <Menu className="h-5 w-5" />
            </SheetTrigger>
            <SheetContent side="right" className="w-[300px] sm:w-[400px] bg-background/60 backdrop-blur-2xl border-l border-border/50 p-8">
              <SheetTitle className="sr-only">Menu</SheetTitle>
              <SheetDescription className="sr-only">Navigation menu</SheetDescription>
              <nav className="flex flex-col gap-2 mt-16 text-2xl font-medium tracking-tight">
                {links.map((link) => (
                  <Link
                    key={link.name}
                    href={link.href}
                    className="group relative px-4 py-4 rounded-2xl text-foreground/70 hover:text-foreground hover:bg-foreground/5 transition-all duration-300 flex items-center justify-between"
                  >
                    <span>{link.name}</span>
                    <span className="opacity-0 -translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300">
                      &rarr;
                    </span>
                  </Link>
                ))}
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
