import * as React from "react"
import { useRouter } from "next/navigation"
import {
    ArrowRight,
    X,
} from "lucide-react"

import {
    CommandDialog,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from "@/components/ui/command"
import { useDemo } from "@/lib/demo-context"

export function CommandMenu({ open, setOpen }) {
    const router = useRouter()
    const { demoLink } = useDemo()

    React.useEffect(() => {
        const down = (e) => {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault()
                setOpen((open) => !open)
            }
        }

        document.addEventListener("keydown", down)
        return () => document.removeEventListener("keydown", down)
    }, [setOpen])

    const runCommand = React.useCallback((path) => {
        setOpen(false)
        router.push(demoLink(path))
    }, [setOpen, router, demoLink])

    return (
        <CommandDialog open={open} onOpenChange={setOpen}>
            <CommandInput placeholder="Search..." className="border-none focus:ring-0">
                <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
                    <kbd className="pointer-events-none inline-flex h-4 select-none items-center gap-1 rounded border bg-muted px-1 font-mono text-[9px] font-medium text-muted-foreground opacity-100">
                        <span className="text-[9px]">ESC</span>
                    </kbd>
                    <button onClick={() => setOpen(false)} className="pointer-events-auto p-0.5 hover:bg-muted rounded-sm transition-colors">
                        <X className="h-3.5 w-3.5 text-muted-foreground" />
                    </button>
                </div>
            </CommandInput>

            <CommandList className="pb-2 max-h-[300px] overflow-y-auto no-scrollbar">
                <CommandEmpty>No results found.</CommandEmpty>
                <CommandGroup heading="Pages" className="text-muted-foreground px-2">
                    <CommandItem onSelect={() => runCommand("/")} className="data-[selected=true]:bg-primary/5 data-[selected=true]:text-primary aria-selected:bg-primary/5 aria-selected:text-primary cursor-pointer group">
                        <ArrowRight className="mr-2 h-4 w-4 text-muted-foreground group-data-[selected=true]:text-primary group-aria-selected:text-primary transition-colors" />
                        <span>Home</span>
                    </CommandItem>
                    <CommandItem onSelect={() => runCommand("/about")} className="data-[selected=true]:bg-primary/5 data-[selected=true]:text-primary aria-selected:bg-primary/5 aria-selected:text-primary cursor-pointer group">
                        <ArrowRight className="mr-2 h-4 w-4 text-muted-foreground group-data-[selected=true]:text-primary group-aria-selected:text-primary transition-colors" />
                        <span>About Us</span>
                    </CommandItem>
                    <CommandItem onSelect={() => runCommand("/contact")} className="data-[selected=true]:bg-primary/5 data-[selected=true]:text-primary aria-selected:bg-primary/5 aria-selected:text-primary cursor-pointer group">
                        <ArrowRight className="mr-2 h-4 w-4 text-muted-foreground group-data-[selected=true]:text-primary group-aria-selected:text-primary transition-colors" />
                        <span>Contact</span>
                    </CommandItem>
                    <CommandItem onSelect={() => runCommand("/book")} className="data-[selected=true]:bg-primary/5 data-[selected=true]:text-primary aria-selected:bg-primary/5 aria-selected:text-primary cursor-pointer group">
                        <ArrowRight className="mr-2 h-4 w-4 text-muted-foreground group-data-[selected=true]:text-primary group-aria-selected:text-primary transition-colors" />
                        <span>Book Appointment</span>
                    </CommandItem>
                    <CommandItem onSelect={() => runCommand("/gallery")} className="data-[selected=true]:bg-primary/5 data-[selected=true]:text-primary aria-selected:bg-primary/5 aria-selected:text-primary cursor-pointer group">
                        <ArrowRight className="mr-2 h-4 w-4 text-muted-foreground group-data-[selected=true]:text-primary group-aria-selected:text-primary transition-colors" />
                        <span>Gallery</span>
                    </CommandItem>
                    <CommandItem onSelect={() => runCommand("/insurance")} className="data-[selected=true]:bg-primary/5 data-[selected=true]:text-primary aria-selected:bg-primary/5 aria-selected:text-primary cursor-pointer group">
                        <ArrowRight className="mr-2 h-4 w-4 text-muted-foreground group-data-[selected=true]:text-primary group-aria-selected:text-primary transition-colors" />
                        <span>Insurance</span>
                    </CommandItem>
                </CommandGroup>

                <CommandGroup heading="Treatments" className="text-muted-foreground px-2">
                    <CommandItem onSelect={() => runCommand("/treatments/cosmetic")} className="data-[selected=true]:bg-primary/5 data-[selected=true]:text-primary aria-selected:bg-primary/5 aria-selected:text-primary cursor-pointer group">
                        <ArrowRight className="mr-2 h-4 w-4 text-muted-foreground group-data-[selected=true]:text-primary group-aria-selected:text-primary transition-colors" />
                        <span>Cosmetic Dentistry</span>
                    </CommandItem>
                    <CommandItem onSelect={() => runCommand("/treatments/orthodontics")} className="data-[selected=true]:bg-primary/5 data-[selected=true]:text-primary aria-selected:bg-primary/5 aria-selected:text-primary cursor-pointer group">
                        <ArrowRight className="mr-2 h-4 w-4 text-muted-foreground group-data-[selected=true]:text-primary group-aria-selected:text-primary transition-colors" />
                        <span>Orthodontics</span>
                    </CommandItem>
                    <CommandItem onSelect={() => runCommand("/treatments/implants")} className="data-[selected=true]:bg-primary/5 data-[selected=true]:text-primary aria-selected:bg-primary/5 aria-selected:text-primary cursor-pointer group">
                        <ArrowRight className="mr-2 h-4 w-4 text-muted-foreground group-data-[selected=true]:text-primary group-aria-selected:text-primary transition-colors" />
                        <span>Dental Implants</span>
                    </CommandItem>
                    <CommandItem onSelect={() => runCommand("/treatments/general")} className="data-[selected=true]:bg-primary/5 data-[selected=true]:text-primary aria-selected:bg-primary/5 aria-selected:text-primary cursor-pointer group">
                        <ArrowRight className="mr-2 h-4 w-4 text-muted-foreground group-data-[selected=true]:text-primary group-aria-selected:text-primary transition-colors" />
                        <span>General Checkups</span>
                    </CommandItem>
                    <CommandItem onSelect={() => runCommand("/treatments/invisalign")} className="data-[selected=true]:bg-primary/5 data-[selected=true]:text-primary aria-selected:bg-primary/5 aria-selected:text-primary cursor-pointer group">
                        <ArrowRight className="mr-2 h-4 w-4 text-muted-foreground group-data-[selected=true]:text-primary group-aria-selected:text-primary transition-colors" />
                        <span>Invisalign</span>
                    </CommandItem>
                    <CommandItem onSelect={() => runCommand("/treatments/surgical")} className="data-[selected=true]:bg-primary/5 data-[selected=true]:text-primary aria-selected:bg-primary/5 aria-selected:text-primary cursor-pointer group">
                        <ArrowRight className="mr-2 h-4 w-4 text-muted-foreground group-data-[selected=true]:text-primary group-aria-selected:text-primary transition-colors" />
                        <span>Surgical</span>
                    </CommandItem>
                    <CommandItem onSelect={() => runCommand("/treatments/pediatric")} className="data-[selected=true]:bg-primary/5 data-[selected=true]:text-primary aria-selected:bg-primary/5 aria-selected:text-primary cursor-pointer group">
                        <ArrowRight className="mr-2 h-4 w-4 text-muted-foreground group-data-[selected=true]:text-primary group-aria-selected:text-primary transition-colors" />
                        <span>Pediatric Dentistry</span>
                    </CommandItem>
                </CommandGroup>
            </CommandList>
        </CommandDialog>
    )
}
