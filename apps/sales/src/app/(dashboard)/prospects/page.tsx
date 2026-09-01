"use client"

import * as React from "react"
import { 
  Search, ListFilter, Check,
  CircleDashed, Activity, User, Calendar, Database, X,
  MoreHorizontal, Globe
} from "lucide-react"

import { Skeleton } from "@/components/ui/skeleton"
import { Checkbox } from "@/components/ui/checkbox"
import { api } from "@/lib/api"
import Link from "next/link"
import { useRouter } from "next/navigation"

import {
  DropdownMenu,
  DropdownMenuItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
  DropdownMenuPortal,
} from "@/components/ui/dropdown-menu"

export interface Prospect {
  id: string
  business_name: string
  location?: string
  website?: string
  phone?: string
  email?: string
  whatsapp?: string
  qualification_status: string // "unqualified", "reviewing", "qualified", "disqualified"
  source?: string
  created_at: string
}

function formatLocation(b: any): string {
  if (!b) return "—"
  if (b.city && b.state && b.country) {
    if (b.city.includes(b.state) || b.city.includes(b.country)) return b.city
    return [b.city, b.state, b.country].filter(Boolean).join(", ")
  }
  if (b.city && b.state) {
    if (b.city.includes(b.state)) return b.city
    return `${b.city}, ${b.state}`
  }
  return b.city || b.address || b.country || "—"
}

export default function ProspectsPage() {
  const router = useRouter()

  const [prospects, setProspects] = React.useState<Prospect[]>([])

  const [loading, setLoading] = React.useState(true)
  const [searchQuery, setSearchQuery] = React.useState("")
  const [statusTab, setStatusTab] = React.useState("all")
  
  // Unified filter state
  const [filters, setFilters] = React.useState({
    qualification: "all",
    website: "all",
    source: "all"
  })

  // Selection state (Desktop only)
  const [selectedProspects, setSelectedProspects] = React.useState<Set<string>>(new Set())

  const fetchProspects = React.useCallback(async () => {
    try {
      const data = await api.get<any[]>("/prospects")
      if (Array.isArray(data)) {
        const mapped: Prospect[] = data.map((b: any) => ({
          id: String(b.id),
          business_name: b.business_name || "Untitled Prospect",
          location: formatLocation(b),
          website: b.website || undefined,
          phone: b.phone || undefined,
          email: b.email || undefined,
          whatsapp: b.phone
            ? (() => {
                const digits = b.phone.replace(/[^0-9]/g, "")
                const clean = digits.startsWith("0") && digits.length === 11 ? digits.slice(1) : digits
                return clean.length === 10 ? `91${clean}` : clean
              })()
            : undefined,
          qualification_status: b.qualification_status ? b.qualification_status.toLowerCase() : "unqualified",
          source: b.source_platform || "discover",
          created_at: b.created_at || new Date().toISOString()
        }))
        setProspects(mapped)
      } else {
        setProspects([])
      }
    } catch {
      setProspects([])
    } finally {
      setLoading(false)
    }
  }, [])

  React.useEffect(() => {
    fetchProspects()
  }, [fetchProspects])

  // Action logger handler
  const handleAction = async (
    prospect: Prospect, 
    actionType: "website" | "call" | "email" | "whatsapp", 
    targetValue: string
  ) => {
    const actionLabels: Record<string, string> = {
      website: "Website visit logged",
      call: "Call logged",
      email: "Email action logged",
      whatsapp: "WhatsApp action logged"
    }

    try {
      const numId = parseInt(prospect.id.replace(/[^0-9]/g, ""), 10)
      if (!isNaN(numId) && numId > 0) {
        if (actionType === "website") {
          await api.post(`/businesses/${numId}/activities`, {
            type: "website_visited",
            channel: "website",
            outcome: "Website visited",
            notes: targetValue
          })
        } else {
          await api.post(`/businesses/${numId}/outreach`, {
            channel: actionType,
            recipient: targetValue,
            status: "initiated",
            notes: `${actionType} initiated`
          })
        }
      }
    } catch {}
  }

  // Single Add to Leads handler
  const handleSingleAddToLeads = async (prospect: Prospect) => {
    const numId = parseInt(prospect.id.replace(/[^0-9]/g, ""), 10)
    
    // Optimistic removal from view
    setProspects(prev => prev.filter(p => p.id !== prospect.id))
    selectedProspects.delete(prospect.id)
    setSelectedProspects(new Set(selectedProspects))

    try {
      if (!isNaN(numId) && numId > 0) {
        await api.post(`/prospects/${numId}/add-to-leads`, {})
      }
    } catch {}
  }

  // Bulk Add to Leads handler
  const handleBulkAddToLeads = async () => {
    const count = selectedProspects.size
    if (count === 0) return

    const idsToAdd = Array.from(selectedProspects)
    const numericIds = idsToAdd.map(id => parseInt(id.replace(/[^0-9]/g, ""), 10)).filter(n => !isNaN(n) && n > 0)

    // Optimistic removal
    setProspects(prev => prev.filter(p => !selectedProspects.has(p.id)))
    setSelectedProspects(new Set())

    try {
      if (numericIds.length > 0) {
        await api.post("/prospects/bulk-add-to-leads", { business_ids: numericIds })
      }
    } catch {}
  }

  // Single Qualification status handler
  const handleSingleQualify = async (id: string, status: string) => {
    setProspects(prev => prev.map(p => p.id === id ? { ...p, qualification_status: status } : p))
    const numId = parseInt(id.replace(/[^0-9]/g, ""), 10)
    try {
      if (!isNaN(numId) && numId > 0) {
        await api.patch(`/prospects/${numId}/qualify`, { qualification_status: status })
      }
    } catch {}
  }

  // Bulk Qualification status handler
  const handleBulkQualify = async (status: string) => {
    const ids = Array.from(selectedProspects)
    setProspects(prev => prev.map(p => selectedProspects.has(p.id) ? { ...p, qualification_status: status } : p))
    selectedProspects.clear()
    setSelectedProspects(new Set())
    for (const id of ids) {
      const numId = parseInt(id.replace(/[^0-9]/g, ""), 10)
      if (!isNaN(numId) && numId > 0) {
        api.patch(`/prospects/${numId}/qualify`, { qualification_status: status }).catch(() => {})
      }
    }
  }

  const handleDeleteSelected = async () => {
    const ids = Array.from(selectedProspects)
    const numericIds = ids.map(id => parseInt(id.replace(/[^0-9]/g, ""), 10)).filter(n => !isNaN(n) && n > 0)
    setProspects(prev => prev.filter(p => !selectedProspects.has(p.id)))
    selectedProspects.clear()
    setSelectedProspects(new Set())
    if (numericIds.length > 0) {
      try {
        await api.post("/businesses/bulk-delete", { business_ids: numericIds })
      } catch {}
    }
  }

  const handleSingleDelete = async (id: string) => {
    setProspects(prev => prev.filter(p => p.id !== id))
    const numId = parseInt(id.replace(/[^0-9]/g, ""), 10)
    if (!isNaN(numId) && numId > 0) {
      try {
        await api.delete(`/businesses/${numId}`)
      } catch {}
    }
  }


  const activeFilterCount = Object.values(filters).filter(v => v !== "all").length

  const updateFilter = (key: keyof typeof filters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const filteredItems = prospects
    .filter((f) => {
      const q = searchQuery.toLowerCase().trim()
      const matchesSearch = !q || 
        f.business_name.toLowerCase().includes(q) || 
        (f.location ?? "").toLowerCase().includes(q) || 
        (f.website ?? "").toLowerCase().includes(q) || 
        (f.phone ?? "").toLowerCase().includes(q) || 
        (f.email ?? "").toLowerCase().includes(q);
      
      const matchesStatusTab = statusTab === "all" || 
        f.qualification_status === statusTab;
      
      const matchesFilterQualification = filters.qualification === "all" || f.qualification_status === filters.qualification;
      const matchesFilterWebsite = filters.website === "all" || 
        (filters.website === "has_website" && Boolean(f.website)) || 
        (filters.website === "no_website" && !f.website);
      const matchesFilterSource = filters.source === "all" || f.source === filters.source;

      return matchesSearch && matchesStatusTab && matchesFilterQualification && matchesFilterWebsite && matchesFilterSource;
    })
    .sort((a, b) => {
      const timeA = new Date(a.created_at).getTime()
      const timeB = new Date(b.created_at).getTime()
      if (timeB !== timeA) return timeB - timeA
      const numA = parseInt(a.id.replace(/[^0-9]/g, ""), 10) || 0
      const numB = parseInt(b.id.replace(/[^0-9]/g, ""), 10) || 0
      return numB - numA
    });

  // Desktop selection helpers
  const isAllVisibleSelected = filteredItems.length > 0 && filteredItems.every(l => selectedProspects.has(l.id))
  const isSomeVisibleSelected = filteredItems.some(l => selectedProspects.has(l.id)) && !isAllVisibleSelected
  const isSelectionMode = selectedProspects.size > 0

  const toggleAllVisible = () => {
    if (isAllVisibleSelected) {
      const newSelected = new Set(selectedProspects)
      filteredItems.forEach(l => newSelected.delete(l.id))
      setSelectedProspects(newSelected)
    } else {
      const newSelected = new Set(selectedProspects)
      filteredItems.forEach(l => newSelected.add(l.id))
      setSelectedProspects(newSelected)
    }
  }

  const toggleProspect = (id: string) => {
    const newSelected = new Set(selectedProspects)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedProspects(newSelected)
  }

  const clearSelection = () => {
    setSelectedProspects(new Set())
  }

  const renderSubMenu = (
    label: string, 
    icon: React.ReactNode, 
    options: { id: string, label: string }[], 
    currentValue: string, 
    onChange: (val: string) => void
  ) => (
    <DropdownMenuSub>
      <DropdownMenuSubTrigger className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500]">
        <div className="flex items-center gap-2">
          {icon}
          <span>{label}</span>
        </div>
      </DropdownMenuSubTrigger>
      <DropdownMenuPortal>
        <DropdownMenuSubContent 
          className="w-48"
          sideOffset={8}
        >
          <div className="flex flex-col gap-1">
            {options.map((opt) => (
              <DropdownMenuItem
                key={opt.id}
                onClick={() => onChange(opt.id)}
                className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] transition-colors outline-none hover:bg-accent/60 text-foreground capitalize"
              >
                <span>{opt.label}</span>
                {currentValue === opt.id && <Check className="size-3.5" />}
              </DropdownMenuItem>
            ))}
          </div>
        </DropdownMenuSubContent>
      </DropdownMenuPortal>
    </DropdownMenuSub>
  )

  const filterDropdownMenu = (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="Filter"
          className="relative flex items-center justify-center size-9 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-colors cursor-pointer shrink-0"
        >
          <ListFilter size={18} />
          {activeFilterCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 size-4 rounded-full bg-primary text-primary-foreground text-[10px] flex items-center justify-center font-bold pointer-events-none">
              {activeFilterCount}
            </span>
          )}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent 
        align="end" 
        className="w-56"
      >
        <div className="flex items-center justify-between px-3 py-1.5 border-b border-border/40 mb-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Filters</span>
          {activeFilterCount > 0 && (
            <button
              onClick={() => setFilters({
                qualification: "all",
                website: "all",
                source: "all"
              })}
              className="text-xs text-primary font-medium hover:underline cursor-pointer"
            >
              Reset
            </button>
          )}
        </div>

        <div className="flex flex-col gap-1">
          {renderSubMenu(
            "Status", 
            <CircleDashed size={16} className="shrink-0 text-muted-foreground" />, 
            [
              { id: "all", label: "All Statuses" },
              { id: "unqualified", label: "Unqualified" },
              { id: "reviewing", label: "Reviewing" },
              { id: "qualified", label: "Qualified" },
              { id: "disqualified", label: "Disqualified" },
            ],
            filters.qualification,
            (v) => updateFilter("qualification", v)
          )}
          
          {renderSubMenu(
            "Website", 
            <Globe size={16} className="shrink-0 text-muted-foreground" />, 
            [
              { id: "all", label: "Any" },
              { id: "has_website", label: "Has Website" },
              { id: "no_website", label: "No Website" },
            ],
            filters.website,
            (v) => updateFilter("website", v)
          )}

          {renderSubMenu(
            "Source", 
            <Database size={16} className="shrink-0 text-muted-foreground" />, 
            [
              { id: "all", label: "All Sources" },
              { id: "discover", label: "Discover" },
              { id: "import", label: "Import" },
              { id: "manual", label: "Manual" },
            ],
            filters.source,
            (v) => updateFilter("source", v)
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )

  return (
    <>
      {/* ─────────────────────────────────────────────────────────────
          MOBILE VIEW (Native Mobile List with Collapsing Header & Action Pills)
          Visible on screen < md (phone view)
         ───────────────────────────────────────────────────────────── */}
      <div className="flex flex-col w-full md:hidden pb-16">
        
        {/* 1. Mobile Header (Stays sticky at top, z-10) */}
        <div className="sticky top-0 z-10 bg-background flex items-center justify-between px-4 pt-4 pb-2">
          <h1 className="text-xl font-bold tracking-tight text-foreground">Prospects</h1>
        </div>



        {/* 2. Search Bar */}
        <div className="relative z-0 px-4 pt-2 pb-4 bg-background">
          <div className="relative w-full group/search">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors" />
            <input
              type="text"
              placeholder="Search prospects…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-10 w-full pl-10 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
            />
          </div>
        </div>

        {/* 3. Sticky Filter Bar */}
        <div className="sticky top-0 z-30 bg-background/95 backdrop-blur-md px-4 py-2.5 border-b border-border/30 flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 min-w-0 flex-1">
            {["all", "unqualified", "reviewing", "qualified", "disqualified"].map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setStatusTab(tab)}
                className={`h-9 px-3.5 rounded-full text-sm capitalize transition-colors cursor-pointer shrink-0 whitespace-nowrap ${
                  statusTab === tab
                    ? "bg-primary text-primary-foreground font-semibold"
                    : "text-muted-foreground hover:text-foreground font-medium"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {filterDropdownMenu}
        </div>

        {/* Mobile Prospect List Rows */}
        <div className="flex flex-col w-full divide-y divide-border/30">
          {loading ? (
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="flex flex-col gap-2 py-3.5 px-4">
                <div className="flex items-center justify-between">
                  <Skeleton className="h-4 w-40 rounded" />
                  <Skeleton className="size-4 rounded-full" />
                </div>
                <Skeleton className="h-3 w-28 rounded" />
                <Skeleton className="h-4 w-20 rounded-full mt-1" />
              </div>
            ))
          ) : filteredItems.length === 0 ? (
            <div className="py-20 text-center text-sm text-muted-foreground">
              No prospects found.
            </div>
          ) : (
            filteredItems.map((prospect) => (
              <div
                key={prospect.id}
                onClick={() => router.push(`/business/${prospect.id}`)}
                className="flex flex-col gap-2 py-3.5 px-4 active:bg-accent/40 transition-colors cursor-pointer"
              >
                <div className="flex items-start justify-between">
                  <div className="flex flex-col min-w-0 pr-3 flex-1">
                    <div className="font-semibold text-[15px] text-foreground truncate leading-tight">
                      {prospect.business_name}
                    </div>
                    {prospect.location && (
                      <div className="text-xs text-muted-foreground truncate mt-0.5">
                        {prospect.location}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[11px] text-muted-foreground">
                      {new Date(prospect.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                    </span>
                    <div onClick={(e) => e.stopPropagation()}>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <button
                            type="button"
                            aria-label="Prospect actions"
                            className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer"
                          >
                            <MoreHorizontal size={18} />
                          </button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent 
                          align="end" 
                          className="w-48"
                        >
                          <div className="flex flex-col gap-1">
                            <DropdownMenuItem
                              onClick={() => handleSingleAddToLeads(prospect)}
                              className="flex items-center min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] text-primary"
                            >
                              <span>Approve</span>
                            </DropdownMenuItem>

                            <DropdownMenuSub>
                              <DropdownMenuSubTrigger className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500]">
                                Qualification
                              </DropdownMenuSubTrigger>
                              <DropdownMenuPortal>
                                <DropdownMenuSubContent className="w-40">
                                  {["unqualified", "reviewing", "qualified", "disqualified"].map((st) => (
                                    <DropdownMenuItem
                                      key={st}
                                      onClick={() => handleSingleQualify(prospect.id, st)}
                                      className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] capitalize"
                                    >
                                      <span>{st}</span>
                                      {prospect.qualification_status === st && <Check className="size-3.5" />}
                                    </DropdownMenuItem>
                                  ))}
                                </DropdownMenuSubContent>
                              </DropdownMenuPortal>
                            </DropdownMenuSub>

                            <DropdownMenuItem
                              onClick={() => handleSingleDelete(prospect.id)}
                              className="flex items-center min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] text-destructive hover:bg-destructive-muted"
                            >
                              Delete
                            </DropdownMenuItem>
                          </div>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                </div>

                {/* Mobile Actionable Contact Buttons */}
                <div 
                  onClick={(e) => e.stopPropagation()} 
                  className="flex items-center gap-2 pt-1 overflow-x-auto no-scrollbar"
                >
                  {prospect.website && (
                    <a
                      href={prospect.website.startsWith("http") ? prospect.website : `https://${prospect.website}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => handleAction(prospect, "website", prospect.website!)}
                      className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-accent/60 hover:bg-accent text-foreground transition-colors shrink-0"
                    >
                      Website
                    </a>
                  )}

                  {prospect.phone && (
                    <a
                      href={`tel:${prospect.phone}`}
                      onClick={() => handleAction(prospect, "call", prospect.phone!)}
                      className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-accent/60 hover:bg-accent text-foreground transition-colors shrink-0"
                    >
                      Call
                    </a>
                  )}

                  {prospect.email && (
                    <a
                      href={`mailto:${prospect.email}`}
                      onClick={() => handleAction(prospect, "email", prospect.email!)}
                      className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-accent/60 hover:bg-accent text-foreground transition-colors shrink-0"
                    >
                      Email
                    </a>
                  )}

                  {(prospect.whatsapp || prospect.phone) && (
                    <button
                      type="button"
                      onClick={() => {
                        const targetPhone = (prospect.whatsapp || prospect.phone || "").replace(/[^0-9]/g, "")
                        window.open(`https://wa.me/${targetPhone}`, "_blank", "noopener,noreferrer")
                        handleAction(prospect, "whatsapp", prospect.whatsapp || prospect.phone!)
                      }}
                      className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-success-muted text-success hover:bg-success/20 transition-colors shrink-0 cursor-pointer"
                    >
                      WhatsApp
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          DESKTOP / TABLET VIEW (Exact Leads Table Layout with Guide Lines & Checkboxes)
          Visible on screen >= md
         ───────────────────────────────────────────────────────────── */}
      <div className="hidden md:flex flex-col gap-8 px-8 lg:px-12 xl:px-16 pt-14 pb-8 max-w-[1600px] w-full mx-auto">
        {/* Top Header Row */}
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold tracking-tight text-foreground">Prospects</h2>
          <div className="flex items-center gap-3">
            {/* Search Input */}
            <div className="relative group/search">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors" />
              <input
                type="text"
                placeholder="Search prospects..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-9 w-44 sm:w-56 pl-9 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
              />
            </div>
          </div>
        </div>

        {/* Page Toolbar (Tabs and Search/Filter or Bulk Actions) */}
        <div className="flex items-center justify-between min-h-9">
          {!isSelectionMode ? (
            <>
              <div className="flex items-center gap-1.5">
                {/* Status Tabs */}
                {["all", "unqualified", "reviewing", "qualified", "disqualified"].map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setStatusTab(tab)}
                    className={`h-9 px-3.5 rounded-full text-sm capitalize transition-colors cursor-pointer ${
                      statusTab === tab
                        ? "bg-secondary text-foreground font-semibold"
                        : "text-muted-foreground hover:text-foreground font-medium"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {/* Filter Control */}
              <div className="flex items-center">
                {filterDropdownMenu}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-between w-full animate-in fade-in duration-150">
              <div className="flex items-center gap-2">
                {/* Primary Approve Button */}
                <button
                  type="button"
                  onClick={handleBulkAddToLeads}
                  className="flex items-center justify-center h-9 px-4 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 active:scale-95 text-sm font-medium transition-all cursor-pointer"
                >
                  <span>Approve</span>
                </button>

                {/* Qualify Dropdown */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button 
                      type="button"
                      className="h-9 px-3.5 rounded-full bg-secondary hover:bg-accent text-sm font-medium text-foreground transition-colors cursor-pointer"
                    >
                      Qualify
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-44">
                    <div className="flex flex-col gap-1">
                      {["unqualified", "reviewing", "qualified", "disqualified"].map((st) => (
                        <DropdownMenuItem
                          key={st}
                          onClick={() => handleBulkQualify(st)}
                          className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] capitalize transition-colors outline-none hover:bg-accent/60 text-foreground"
                        >
                          {st}
                        </DropdownMenuItem>
                      ))}
                    </div>
                  </DropdownMenuContent>
                </DropdownMenu>

                {/* Delete Button */}
                <button 
                  type="button"
                  onClick={handleDeleteSelected}
                  className="h-9 px-3.5 rounded-full border border-destructive/30 text-destructive hover:bg-destructive-muted text-sm font-medium transition-colors cursor-pointer"
                >
                  Delete
                </button>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground font-normal">
                  {selectedProspects.size} selected
                </span>
                <button
                  type="button"
                  onClick={clearSelection}
                  className="flex items-center justify-center size-7 rounded-full hover:bg-accent text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                  title="Clear selection"
                >
                  <X size={20} />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Main Table / List Container (Identical to Leads Page) */}
        <div className="flex flex-col -ml-12 w-[calc(100%+3rem)] overflow-x-auto">
          {/* Table Header Row: Business | Location | Website | Phone | Email | WhatsApp | Added */}
          <div className="flex items-center group/header w-full pb-2.5 select-none min-w-[900px]">
            {/* Checkbox Gutter Column */}
            <div className="w-9 shrink-0 flex items-center justify-center">
              <div 
                className={`transition-opacity duration-150 ${
                  isSelectionMode ? "opacity-100" : "opacity-0 group-hover/header:opacity-100 hover:opacity-100"
                }`}
              >
                <Checkbox 
                  checked={isAllVisibleSelected ? true : isSomeVisibleSelected ? 'indeterminate' : false}
                  onCheckedChange={toggleAllVisible}
                  aria-label="Select all visible prospects"
                />
              </div>
            </div>

            {/* Column Titles */}
            <div className="flex-1 grid grid-cols-[minmax(180px,2fr)_minmax(140px,1.4fr)_minmax(140px,1.3fr)_minmax(140px,1.3fr)_minmax(170px,1.5fr)_minmax(90px,0.9fr)_minmax(80px,0.8fr)] gap-4 px-3 text-[14px] font-medium text-muted-foreground items-center">
              <div>Business</div>
              <div>Location</div>
              <div>Website</div>
              <div>Phone</div>
              <div>Email</div>
              <div>WhatsApp</div>
              <div className="text-right">Added</div>
            </div>
          </div>

          {/* Table Body Rows */}
          <div className="flex flex-col w-full min-w-[900px]">
            {loading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="flex items-center w-full py-2.5">
                  <div className="w-9 shrink-0 flex items-center justify-center">
                    <Skeleton className="size-4 rounded" />
                  </div>
                  <div className="flex-1 grid grid-cols-[minmax(180px,2fr)_minmax(140px,1.4fr)_minmax(140px,1.3fr)_minmax(140px,1.3fr)_minmax(170px,1.5fr)_minmax(90px,0.9fr)_minmax(80px,0.8fr)] gap-4 px-3 items-center">
                    <Skeleton className="h-4 rounded" />
                    <Skeleton className="h-4 rounded" />
                    <Skeleton className="h-4 rounded" />
                    <Skeleton className="h-4 rounded" />
                    <Skeleton className="h-4 rounded" />
                    <Skeleton className="h-4 rounded" />
                    <Skeleton className="h-4 rounded" />
                  </div>
                </div>
              ))
            ) : filteredItems.length === 0 ? (
              <div className="py-16 text-center text-sm text-muted-foreground">
                No prospects found.
              </div>
            ) : (
              filteredItems.map((prospect, idx) => {
                const isSelected = selectedProspects.has(prospect.id)
                const prevSelected = idx > 0 && selectedProspects.has(filteredItems[idx - 1].id)
                const nextSelected = idx < filteredItems.length - 1 && selectedProspects.has(filteredItems[idx + 1].id)

                let selectionRounding = "rounded-xl"
                if (isSelected) {
                  if (!prevSelected && nextSelected) {
                    selectionRounding = "rounded-t-xl border-b border-border/40"
                  } else if (prevSelected && nextSelected) {
                    selectionRounding = "rounded-none border-b border-border/40"
                  } else if (prevSelected && !nextSelected) {
                    selectionRounding = "rounded-b-xl"
                  } else {
                    selectionRounding = "rounded-xl"
                  }
                }

                return (
                  <div 
                    key={prospect.id}
                    className="flex items-center group/row w-full my-[1px] relative"
                  >
                    {/* Dedicated Checkbox Left Gutter */}
                    <div className="w-9 shrink-0 flex items-center justify-center">
                      <div 
                        className={`transition-opacity duration-150 ${
                          isSelected 
                            ? "opacity-100" 
                            : "opacity-0 group-hover/row:opacity-100 hover:opacity-100"
                        }`}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Checkbox 
                          checked={isSelected}
                          onCheckedChange={() => toggleProspect(prospect.id)}
                          aria-label={`Select ${prospect.business_name}`}
                        />
                      </div>
                    </div>

                    {/* Main Row Content Capsule */}
                    <div 
                      onClick={() => toggleProspect(prospect.id)}
                      className={`flex-1 grid grid-cols-[minmax(180px,2fr)_minmax(140px,1.4fr)_minmax(140px,1.3fr)_minmax(140px,1.3fr)_minmax(170px,1.5fr)_minmax(90px,0.9fr)_minmax(80px,0.8fr)] gap-4 px-3 py-3 text-sm items-center transition-colors cursor-pointer ${
                        isSelected 
                          ? `bg-secondary text-foreground ${selectionRounding}` 
                          : "hover:bg-accent/50 rounded-xl"
                      }`}
                    >
                      {/* 1. Business */}
                      <div className="flex items-center min-w-0">
                        <Link 
                          href={`/business/${prospect.id}`}
                          onClick={(e) => e.stopPropagation()} 
                          className="font-medium text-foreground hover:text-primary transition-colors truncate"
                          title={prospect.business_name}
                        >
                          {prospect.business_name}
                        </Link>
                      </div>

                      {/* 2. Location */}
                      <div className="text-muted-foreground text-xs truncate" title={prospect.location || "—"}>
                        {prospect.location || "—"}
                      </div>

                      {/* 3. Website */}
                      <div className="min-w-0">
                        {prospect.website ? (
                          <a
                            href={prospect.website.startsWith("http") ? prospect.website : `https://${prospect.website}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleAction(prospect, "website", prospect.website!)
                            }}
                            className="inline-flex items-center text-xs text-muted-foreground hover:text-foreground hover:underline truncate transition-colors max-w-full group/link py-1 px-1.5 -ml-1.5 rounded-lg hover:bg-accent/50"
                            title={`Open ${prospect.website}`}
                          >
                            <span className="truncate">{prospect.website.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')}</span>
                          </a>
                        ) : (
                          <span className="text-xs text-muted-foreground/40">—</span>
                        )}
                      </div>

                      {/* 4. Phone */}
                      <div className="min-w-0">
                        {prospect.phone ? (
                          <a
                            href={`tel:${prospect.phone}`}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleAction(prospect, "call", prospect.phone!)
                            }}
                            className="inline-flex items-center text-xs text-muted-foreground hover:text-foreground hover:underline truncate transition-colors max-w-full group/phone py-1 px-1.5 -ml-1.5 rounded-lg hover:bg-accent/50"
                            title={`Call ${prospect.phone}`}
                          >
                            <span className="truncate">{prospect.phone}</span>
                          </a>
                        ) : (
                          <span className="text-xs text-muted-foreground/40">—</span>
                        )}
                      </div>

                      {/* 5. Email */}
                      <div className="min-w-0">
                        {prospect.email ? (
                          <a
                            href={`mailto:${prospect.email}`}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleAction(prospect, "email", prospect.email!)
                            }}
                            className="inline-flex items-center text-xs text-muted-foreground hover:text-foreground hover:underline truncate transition-colors max-w-full group/email py-1 px-1.5 -ml-1.5 rounded-lg hover:bg-accent/50"
                            title={`Email ${prospect.email}`}
                          >
                            <span className="truncate">{prospect.email}</span>
                          </a>
                        ) : (
                          <span className="text-xs text-muted-foreground/40">—</span>
                        )}
                      </div>

                      {/* 6. WhatsApp */}
                      <div className="min-w-0">
                        {(prospect.whatsapp || prospect.phone) ? (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              const targetNumber = (prospect.whatsapp || prospect.phone || "").replace(/[^0-9]/g, "")
                              window.open(`https://wa.me/${targetNumber}`, "_blank", "noopener,noreferrer")
                              handleAction(prospect, "whatsapp", prospect.whatsapp || prospect.phone!)
                            }}
                            className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-success-muted text-success hover:bg-success/20 active:scale-95 transition-all cursor-pointer"
                            title={`Chat on WhatsApp (${prospect.whatsapp || prospect.phone})`}
                          >
                            <span>Chat</span>
                          </button>
                        ) : (
                          <span className="text-xs text-muted-foreground/40">—</span>
                        )}
                      </div>

                      {/* 7. Added */}
                      <div className="text-xs text-muted-foreground text-right truncate">
                        {new Date(prospect.created_at).toLocaleDateString(undefined, {
                          month: "short",
                          day: "numeric",
                        })}
                      </div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      </div>
    </>
  )
}
