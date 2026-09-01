"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { ChevronDown, X } from "lucide-react"

import { LocationSelector, StructuredLocation } from "@/components/location-selector"


import { cn } from "@/lib/utils"
import { api } from "@/lib/api"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import { Command as CommandPrimitive } from "cmdk"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

const BUSINESS_CATEGORIES = [
  "Dental Clinics",
  "Software Companies",
  "Real Estate Agencies",
  "Law Firms",
  "Accounting Firms",
  "Marketing Agencies",
  "Plumbing Services",
  "Restaurants",
  "Hotels",
]

export default function DiscoverPage() {
  const router = useRouter()
  // 0: Business, 1: Location, 2: Discovering
  const [step, setStep] = React.useState(0)


  
  const [business, setBusiness] = React.useState("")
  const [businessOpen, setBusinessOpen] = React.useState(false)
  const [businessSearch, setBusinessSearch] = React.useState("")
  const [businessError, setBusinessError] = React.useState("")

  const [location, setLocation] = React.useState<StructuredLocation | null>(null)
  const [locationError, setLocationError] = React.useState("")

  const handleContinueBusiness = () => {
    if (!business) {
      setBusinessError("Select a business type")
      return
    }
    setBusinessError("")
    setStep(1)
  }

  const [jobId, setJobId] = React.useState<string | null>(null)

  const handleContinueLocation = async () => {
    if (!location) {
      setLocationError("Select a location")
      return
    }
    setLocationError("")
    setStep(2)

    try {
      const res = await api.post<{ job_id: string; status: string }>("/prospecting/jobs", {
        business_type: business,
        location: {
          country: location.country || undefined,
          state: location.region || undefined,
          city: location.city || undefined,
        },
        website_status: "any"
      })
      if (res && res.job_id) {
        setJobId(res.job_id)
      }
    } catch {
      // Fallback
    }
  }

  // Poll discovery job until completion, then route to /prospects
  React.useEffect(() => {
    if (step !== 2) return

    let isSubscribed = true
    const startTime = Date.now()

    const interval = setInterval(async () => {
      // Extended safety timeout after 180s (3 minutes) for live web scraping
      if (Date.now() - startTime > 180000) {
        clearInterval(interval)
        if (isSubscribed) {
          router.push("/prospects")
          router.refresh()
        }
        return
      }

      if (!jobId) return

      try {
        const job = await api.get<{ status: string; new_leads?: number; total_processed?: number }>(`/prospecting/jobs/${jobId}`)
        if (!isSubscribed) return

        if (job && (job.status === "completed" || job.status === "failed")) {
          clearInterval(interval)
          setTimeout(() => {
            if (isSubscribed) {
              router.push("/prospects")
              router.refresh()
            }
          }, 600)
        }
      } catch {
        // Continue polling until timeout
      }
    }, 1500)

    return () => {
      isSubscribed = false
      clearInterval(interval)
    }
  }, [step, jobId, router])

  const renderContent = () => {
    switch (step) {
      case 0:
        return (
          <>
            <h1 className="text-[18px] leading-[26px] font-semibold text-foreground mb-[24px] transition-colors duration-300">
              Find the businesses you need
            </h1>
            
            <div className="w-full max-w-[280px] mb-[24px] text-left">
              <Popover 
                open={businessOpen} 
                onOpenChange={(open) => {
                  setBusinessOpen(open)
                  if (open && businessError) setBusinessError("")
                }}
              >
                <PopoverTrigger asChild>
                  <button
                    type="button"
                    aria-expanded={businessOpen}
                    className={cn(
                      "flex items-center justify-between w-full h-[44px] px-5 rounded-full bg-accent/50 hover:bg-accent/80 text-[15px] focus:outline-none focus:ring-2 focus:ring-foreground/20 transition-all group cursor-pointer",
                      businessError && "ring-2 ring-destructive/80 focus:ring-destructive/80",
                      businessOpen && "opacity-0 pointer-events-none"
                    )}
                  >
                    <div className="flex items-center min-w-0 flex-1">
                      <span className={cn("truncate font-medium", !business && "text-muted-foreground/60")}>
                        {business || "Select business type"}
                      </span>
                    </div>
                    <ChevronDown size={16} className="text-muted-foreground ml-2 shrink-0 opacity-50" />
                  </button>
                </PopoverTrigger>
                <PopoverContent 
                  className="w-[var(--radix-popover-trigger-width)] p-0 rounded-[22px] shadow-none overflow-hidden border-none bg-popover text-popover-foreground" 
                  align="start" 
                  side="bottom"
                  sideOffset={-44}
                >
                  <Command>
                    <div className="flex items-center w-full h-[44px] px-5 border-b border-border/40">
                      <CommandPrimitive.Input 
                        placeholder="Search business types..." 
                        value={businessSearch}
                        onValueChange={setBusinessSearch}
                        className="flex-1 bg-transparent text-[15px] font-medium outline-none placeholder:text-muted-foreground/60 placeholder:font-medium"
                        autoFocus
                      />
                      <button type="button" onClick={() => setBusinessOpen(false)} className="ml-2 text-muted-foreground shrink-0 opacity-50 hover:opacity-100 transition-opacity">
                        <X size={16} />
                      </button>
                    </div>
                    <CommandList className="max-h-[280px] overflow-y-auto no-scrollbar p-1.5">
                      <CommandEmpty className="py-6 text-center text-[15px] text-muted-foreground">No business types found.</CommandEmpty>
                      <CommandGroup>
                        {BUSINESS_CATEGORIES.map((cat) => (
                          <CommandItem
                            key={cat}
                            value={cat}
                            onSelect={(val) => {
                              const originalCat = BUSINESS_CATEGORIES.find(c => c.toLowerCase() === val) || cat;
                              setBusiness(originalCat)
                              setBusinessError("")
                              setBusinessOpen(false)
                            }}
                            className={cn(
                              "flex items-center px-3.5 py-2.5 cursor-pointer rounded-[14px] font-medium text-[15px] transition-colors mb-0.5",
                              business === cat ? "bg-accent/60 text-foreground" : "text-muted-foreground hover:bg-accent/40 hover:text-foreground aria-selected:bg-accent/40 aria-selected:text-foreground"
                            )}
                          >
                            {cat}
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
              {businessError && (
                <p className="text-[13px] text-destructive font-medium mt-2 px-1 text-center animate-in fade-in slide-in-from-top-1 duration-200">
                  {businessError}
                </p>
              )}
            </div>

            <div className="flex flex-col items-center w-full gap-[12px]">
              <button
                type="button"
                onClick={handleContinueBusiness}
                className="h-[44px] w-full max-w-[280px] rounded-full bg-primary text-primary-foreground hover:bg-primary/90 active:scale-[0.98] transition-all font-semibold text-[15px] cursor-pointer"
              >
                Continue
              </button>
            </div>
          </>
        )
      
      case 1:
        return (
          <>
            <h1 className="text-[18px] leading-[26px] font-semibold text-foreground mb-[24px] transition-colors duration-300">
              Choose a location
            </h1>
            
            <div className="w-full max-w-[280px] mb-[24px] text-left">
              <LocationSelector 
                value={location}
                onChange={(loc: StructuredLocation | null) => {
                  setLocation(loc)
                  if (locationError) setLocationError("")
                }}
                className={cn(locationError && "ring-2 ring-destructive/80 focus:ring-destructive/80")}
              />
              {locationError && (
                <p className="text-[13px] text-destructive font-medium mt-2 px-1 text-center animate-in fade-in slide-in-from-top-1 duration-200">
                  {locationError}
                </p>
              )}
            </div>

            <div className="flex flex-col items-center w-full gap-[12px]">
              <button
                type="button"
                onClick={handleContinueLocation}
                className="h-[44px] w-full max-w-[280px] rounded-full bg-primary text-primary-foreground hover:bg-primary/90 active:scale-[0.98] transition-all font-semibold text-[15px] cursor-pointer"
              >
                Continue
              </button>
            </div>
          </>
        )

      case 2:
        return (
          <>
            <h1 className="text-[18px] leading-[26px] font-semibold text-foreground mb-[24px] transition-colors duration-300">
              Finding businesses
            </h1>
            
            <div className="w-full max-w-[380px] flex flex-col gap-4 mb-[24px] animate-in fade-in duration-300">
              <div className="w-full h-1 bg-muted rounded-full relative overflow-hidden">
                <div className="absolute inset-0 bg-primary/50 w-1/3 animate-progress-slide rounded-full" />
              </div>
            </div>
          </>
        )
    }
  }

  return (
    <div className="flex flex-col h-full w-full min-h-screen">
      {/* Mobile Sticky Header */}
      <div className="md:hidden sticky top-0 z-10 bg-background flex items-center justify-between px-4 pt-4 pb-2 border-b border-border/30">
        <h1 className="text-xl font-bold tracking-tight text-foreground">Discover</h1>
      </div>


      {/* Content Container */}
      <div className="flex flex-col flex-1 px-4 md:px-8 lg:px-12 xl:px-16 pt-4 md:pt-14 pb-8 max-w-[1600px] mx-auto w-full">
        {/* Desktop Header */}
        <div className="hidden md:flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold tracking-tight text-foreground">Discover</h2>
        </div>


        {/* Empty State Geometry */}
        <div className="flex-1 flex flex-col items-center pt-[24vh] md:pt-[28vh] pb-8 px-4 w-full relative">
          <div className="flex flex-col items-center w-full max-w-[420px] text-center">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  )
}
