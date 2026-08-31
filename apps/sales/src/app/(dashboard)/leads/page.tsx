"use client"

import * as React from "react"
import { 
  Search, ListFilter, Check,
  CircleDashed, Activity, User, Calendar, Database, X,
  MoreHorizontal, Phone, MessageSquare, Mail, AlertTriangle, ArrowRight,
  TrendingUp, Clock
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
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

export interface Lead {
  id: string
  business_name: string
  location?: string
  website?: string
  phone?: string
  email?: string
  whatsapp?: string
  status: string
  priority?: string
  signal?: string
  owner?: string
  source?: string
  follow_up?: string
  created_at: string
}

const STATUS_VARIANTS: Record<string, "default" | "secondary" | "outline"> = {
  new: "default",
  contacted: "secondary",
  qualified: "secondary",
  negotiating: "secondary",
  won: "default",
  lost: "outline",
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

export default function LeadsPage() {
  const router = useRouter()

  const [leads, setLeads] = React.useState<Lead[]>([])

  const [loading, setLoading] = React.useState(true)
  const [searchQuery, setSearchQuery] = React.useState("")
  const [statusTab, setStatusTab] = React.useState("all")
  
  // Unified filter state
  const [filters, setFilters] = React.useState({
    status: "all",
    signal: "all",
    owner: "all",
    followUp: "all",
    source: "all"
  })

  // Selection state (Desktop only)
  const [selectedLeads, setSelectedLeads] = React.useState<Set<string>>(new Set())

  React.useEffect(() => {
    api.get<Lead[]>("/leads")
      .then((data) => {
        if (Array.isArray(data)) {
          const mapped: Lead[] = data.map((b: any) => ({
            id: String(b.id),
            business_name: b.business_name || "Untitled Lead",
            location: formatLocation(b),
            website: b.website || undefined,
            phone: b.phone || undefined,
            email: b.email || undefined,
            whatsapp: b.phone ? b.phone.replace(/[^0-9]/g, "") : undefined,
            status: b.pipeline_stage ? b.pipeline_stage.toLowerCase() : "new",
            priority: b.priority || "medium",
            signal: b.signal || "warm",
            owner: "me",
            source: b.source_platform || "discover",
            follow_up: "None",
            created_at: b.created_at || new Date().toISOString()
          }))
          setLeads(mapped)
        } else {
          setLeads([])
        }
      })
      .catch(() => setLeads([]))
      .finally(() => setLoading(false))
  }, [])

  // Action logger handler
  const handleAction = async (
    lead: Lead, 
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

      const numId = parseInt(lead.id.replace(/[^0-9]/g, ""), 10)
      if (!isNaN(numId) && numId > 0) {
        const typeMap: Record<string, string> = {
          website: "website_visited",
          call: "call_initiated",
          whatsapp: "whatsapp_opened",
          email: "email_initiated"
        }
        await api.post(`/businesses/${numId}/activities`, {
          type: typeMap[actionType] || actionType,
          channel: actionType,
          outcome: `${actionType} initiated`,
          notes: `User initiated ${actionType} action for ${lead.business_name} (${targetValue})`
        })
      }
    } catch {
      // Graceful fallback for mock data/offline
    }
  }

  const activeFilterCount = Object.values(filters).filter(v => v !== "all").length

  const updateFilter = (key: keyof typeof filters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const filteredItems = leads.filter((f) => {
    const q = searchQuery.toLowerCase().trim()
    const matchesSearch = !q || 
      f.business_name.toLowerCase().includes(q) || 
      (f.location ?? "").toLowerCase().includes(q) || 
      (f.website ?? "").toLowerCase().includes(q) || 
      (f.phone ?? "").toLowerCase().includes(q) || 
      (f.email ?? "").toLowerCase().includes(q);
    
    const matchesStatusTab = statusTab === "all" || 
      (statusTab === "new" && f.status === "new") ||
      (statusTab === "active" && (f.status === "contacted" || f.status === "qualified" || f.status === "negotiating")) ||
      (statusTab === "closed" && (f.status === "won" || f.status === "lost"));
    
    const matchesFilterStatus = filters.status === "all" || f.status === filters.status;
    const matchesFilterSignal = filters.signal === "all" || f.signal === filters.signal;
    const matchesFilterOwner = filters.owner === "all" || f.owner === filters.owner;
    const matchesFilterSource = filters.source === "all" || f.source === filters.source;
    const matchesFilterFollowUp = filters.followUp === "all" || f.follow_up === filters.followUp;

    return matchesSearch && matchesStatusTab && matchesFilterStatus && matchesFilterSignal && matchesFilterOwner && matchesFilterSource && matchesFilterFollowUp;
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
  const isAllVisibleSelected = filteredItems.length > 0 && filteredItems.every(l => selectedLeads.has(l.id))
  const isSomeVisibleSelected = filteredItems.some(l => selectedLeads.has(l.id)) && !isAllVisibleSelected
  const isSelectionMode = selectedLeads.size > 0

  const toggleAllVisible = () => {
    if (isAllVisibleSelected) {
      const newSelected = new Set(selectedLeads)
      filteredItems.forEach(l => newSelected.delete(l.id))
      setSelectedLeads(newSelected)
    } else {
      const newSelected = new Set(selectedLeads)
      filteredItems.forEach(l => newSelected.add(l.id))
      setSelectedLeads(newSelected)
    }
  }

  const toggleLead = (id: string) => {
    const newSelected = new Set(selectedLeads)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedLeads(newSelected)
  }

  const clearSelection = () => {
    setSelectedLeads(new Set())
  }

  // Bulk handlers (Desktop)
  const handleBulkStatusChange = (newStatus: string) => {
    setLeads(leads.map(l => selectedLeads.has(l.id) ? { ...l, status: newStatus } : l))
    clearSelection()
  }

  const handleBulkFollowUp = (followUpTime: string) => {
    setLeads(leads.map(l => selectedLeads.has(l.id) ? { ...l, follow_up: followUpTime } : l))
    clearSelection()
  }

  const handleBulkReminder = (reminderTime: string) => {
    setLeads(leads.map(l => selectedLeads.has(l.id) ? { ...l, follow_up: `Reminder: ${reminderTime}` } : l))
    clearSelection()
  }

  const handleDeleteSelected = () => {
    setLeads(leads.filter(l => !selectedLeads.has(l.id)))
    clearSelection()
  }

  // Single item action handlers (Mobile ⋯ menu)
  const handleSingleStatusChange = (id: string, newStatus: string) => {
    setLeads(leads.map(l => l.id === id ? { ...l, status: newStatus } : l))
  }

  const handleSingleFollowUp = (id: string, followUpTime: string) => {
    setLeads(leads.map(l => l.id === id ? { ...l, follow_up: followUpTime } : l))
  }

  const handleSingleReminder = (id: string, reminderTime: string) => {
    setLeads(leads.map(l => l.id === id ? { ...l, follow_up: `Reminder: ${reminderTime}` } : l))
  }

  const handleSingleDelete = (id: string) => {
    setLeads(leads.filter(l => l.id !== id))
  }

  const renderSubMenu = (
    label: string, 
    icon: React.ReactNode, 
    options: { id: string, label: string }[], 
    currentValue: string, 
    onChange: (val: string) => void
  ) => (
    <DropdownMenuSub>
      <DropdownMenuSubTrigger className="flex items-center gap-3 min-h-9 px-2.5 rounded-2xl cursor-pointer text-[14px] font-[500] hover:bg-accent/60 data-[state=open]:bg-accent/60">
        {icon}
        {label}
      </DropdownMenuSubTrigger>
      <DropdownMenuPortal>
        <DropdownMenuSubContent 
          className="w-48 p-2 rounded-3xl border border-border/40 shadow-xl bg-background"
          sideOffset={8}
        >
          <div className="flex flex-col gap-1">
            {options.map((opt) => (
              <DropdownMenuItem
                key={opt.id}
                onClick={() => onChange(opt.id)}
                className="flex items-center justify-between min-h-9 px-2.5 rounded-2xl cursor-pointer text-[14px] font-[500] transition-colors outline-none border-none hover:bg-accent/60 text-foreground"
              >
                {opt.label}
                {currentValue === opt.id && <Check size={20} className="shrink-0" />}
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
            <span className="absolute -top-0.5 -right-0.5 size-4 rounded-full bg-neutral-900 text-white dark:bg-white dark:text-black text-[10px] flex items-center justify-center font-bold shadow-sm pointer-events-none">
              {activeFilterCount}
            </span>
          )}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent 
        align="end" 
        className="w-56 p-2 rounded-3xl border border-border/40 shadow-xl bg-background"
      >
        <div className="flex items-center justify-between px-3 py-1.5 border-b border-border/40 mb-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Filters</span>
          {activeFilterCount > 0 && (
            <button
              onClick={() => setFilters({
                status: "all",
                signal: "all",
                owner: "all",
                followUp: "all",
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
            <CircleDashed size={20} className="shrink-0 text-muted-foreground" />, 
            [
              { id: "all", label: "All Statuses" },
              { id: "new", label: "New" },
              { id: "contacted", label: "Contacted" },
              { id: "qualified", label: "Qualified" },
              { id: "negotiating", label: "Negotiating" },
              { id: "won", label: "Won" },
              { id: "lost", label: "Lost" },
            ],
            filters.status,
            (v) => updateFilter("status", v)
          )}
          
          {renderSubMenu(
            "Signal", 
            <Activity size={20} className="shrink-0 text-muted-foreground" />, 
            [
              { id: "all", label: "All Signals" },
              { id: "hot", label: "Hot" },
              { id: "warm", label: "Warm" },
              { id: "cold", label: "Cold" },
            ],
            filters.signal,
            (v) => updateFilter("signal", v)
          )}

          {renderSubMenu(
            "Owner", 
            <User size={20} className="shrink-0 text-muted-foreground" />, 
            [
              { id: "all", label: "Any Owner" },
              { id: "unassigned", label: "Unassigned" },
              { id: "me", label: "Assigned to me" },
            ],
            filters.owner,
            (v) => updateFilter("owner", v)
          )}

          {renderSubMenu(
            "Follow-up", 
            <Calendar size={20} className="shrink-0 text-muted-foreground" />, 
            [
              { id: "all", label: "Any Time" },
              { id: "overdue", label: "Overdue" },
              { id: "today", label: "Due today" },
              { id: "upcoming", label: "Upcoming" },
              { id: "none", label: "None" },
            ],
            filters.followUp,
            (v) => updateFilter("followUp", v)
          )}

          {renderSubMenu(
            "Source", 
            <Database size={20} className="shrink-0 text-muted-foreground" />, 
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
          <h1 className="text-xl font-bold tracking-tight text-foreground">Leads</h1>
        </div>



        {/* 2. Search Bar */}
        <div className="relative z-0 px-4 pt-2 pb-4 bg-background">
          <div className="relative w-full group/search">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors" />
            <input
              type="text"
              placeholder="Search leads…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-10 w-full pl-10 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
            />
          </div>
        </div>

        {/* 3. Sticky Filter Bar */}
        <div className="sticky top-0 z-30 bg-background/95 backdrop-blur-md px-4 py-2.5 border-b border-border/30 flex items-center justify-between gap-2 shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 min-w-0 flex-1">
            {["all", "new", "active", "closed"].map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setStatusTab(tab)}
                className={`h-9 px-3.5 rounded-full text-sm capitalize transition-colors cursor-pointer shrink-0 whitespace-nowrap ${
                  statusTab === tab
                    ? "bg-neutral-900 text-white dark:bg-white dark:text-black font-semibold shadow-sm"
                    : "text-muted-foreground hover:text-foreground font-medium"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {filterDropdownMenu}
        </div>

        {/* Mobile Lead List Rows */}
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
              No leads found.
            </div>
          ) : (
            filteredItems.map((lead) => (
              <div
                key={lead.id}
                onClick={() => router.push(`/business/${lead.id}`)}
                className="flex flex-col gap-2 py-3.5 px-4 active:bg-accent/40 transition-colors cursor-pointer"
              >
                <div className="flex items-start justify-between">
                  <div className="flex flex-col min-w-0 pr-3 flex-1">
                    <div className="font-semibold text-[15px] text-foreground truncate leading-tight">
                      {lead.business_name}
                    </div>
                    {lead.location && (
                      <div className="text-xs text-muted-foreground truncate mt-0.5">
                        {lead.location}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[11px] text-muted-foreground">
                      {new Date(lead.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                    </span>
                    <div onClick={(e) => e.stopPropagation()}>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <button
                            type="button"
                            aria-label="Lead actions"
                            className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer"
                          >
                            <MoreHorizontal size={18} />
                          </button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent 
                          align="end" 
                          className="w-48 p-2 rounded-2xl border border-border/40 shadow-xl bg-background"
                        >
                          <div className="flex flex-col gap-1">
                            <DropdownMenuSub>
                              <DropdownMenuSubTrigger className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500]">
                                Change Status
                              </DropdownMenuSubTrigger>
                              <DropdownMenuPortal>
                                <DropdownMenuSubContent className="w-40 p-2 rounded-2xl border border-border/40 shadow-xl bg-background">
                                  {["new", "contacted", "qualified", "proposal", "won", "lost"].map((st) => (
                                    <DropdownMenuItem
                                      key={st}
                                      onClick={() => handleSingleStatusChange(lead.id, st)}
                                      className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] capitalize"
                                    >
                                      {st}
                                      {lead.status === st && <Check className="size-3.5" />}
                                    </DropdownMenuItem>
                                  ))}
                                </DropdownMenuSubContent>
                              </DropdownMenuPortal>
                            </DropdownMenuSub>

                            <DropdownMenuItem
                              onClick={() => handleSingleDelete(lead.id)}
                              className="flex items-center min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30"
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
                  {lead.website && (
                    <a
                      href={lead.website.startsWith("http") ? lead.website : `https://${lead.website}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => handleAction(lead, "website", lead.website!)}
                      className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-accent/60 hover:bg-accent text-foreground transition-colors shrink-0"
                    >
                      Website
                    </a>
                  )}

                  {lead.phone && (
                    <a
                      href={`tel:${lead.phone}`}
                      onClick={() => handleAction(lead, "call", lead.phone!)}
                      className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-accent/60 hover:bg-accent text-foreground transition-colors shrink-0"
                    >
                      Call
                    </a>
                  )}

                  {lead.email && (
                    <a
                      href={`mailto:${lead.email}`}
                      onClick={() => handleAction(lead, "email", lead.email!)}
                      className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-accent/60 hover:bg-accent text-foreground transition-colors shrink-0"
                    >
                      Email
                    </a>
                  )}

                  {(lead.whatsapp || lead.phone) && (
                    <button
                      type="button"
                      onClick={() => {
                        const targetPhone = (lead.whatsapp || lead.phone || "").replace(/[^0-9]/g, "")
                        window.open(`https://wa.me/${targetPhone}`, "_blank", "noopener,noreferrer")
                        handleAction(lead, "whatsapp", lead.whatsapp || lead.phone!)
                      }}
                      className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/20 transition-colors shrink-0 cursor-pointer"
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
          DESKTOP / TABLET VIEW (Full table with guide lines & checkboxes)
          Visible on screen >= md
         ───────────────────────────────────────────────────────────── */}
      <div className="hidden md:flex flex-col gap-8 px-8 lg:px-12 xl:px-16 pt-14 pb-8 max-w-[1600px] w-full mx-auto">
        {/* Top Header Row */}
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold tracking-tight text-foreground">Leads</h2>
          <div className="flex items-center gap-3">
            {/* Search Input */}
            <div className="relative group/search">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors" />
              <input
                type="text"
                placeholder="Search leads..."
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
                {["all", "new", "active", "closed"].map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setStatusTab(tab)}
                    className={`h-9 px-3.5 rounded-full text-sm capitalize transition-colors cursor-pointer ${
                      statusTab === tab
                        ? "bg-neutral-100 dark:bg-neutral-800 text-foreground font-semibold"
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
                {/* Change Status Dropdown */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button 
                      type="button"
                      className="h-9 px-3.5 rounded-full bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-sm font-medium text-foreground transition-colors cursor-pointer"
                    >
                      Change Status
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-44 p-2 rounded-2xl border border-border/40 shadow-xl bg-background">
                    <div className="flex flex-col gap-1">
                      {["new", "contacted", "qualified", "proposal", "won", "lost"].map((st) => (
                        <DropdownMenuItem
                          key={st}
                          onClick={() => handleBulkStatusChange(st)}
                          className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] capitalize transition-colors outline-none hover:bg-accent/60 text-foreground"
                        >
                          {st}
                        </DropdownMenuItem>
                      ))}
                    </div>
                  </DropdownMenuContent>
                </DropdownMenu>

                {/* Add Follow-up Dropdown */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button 
                      type="button"
                      className="h-9 px-3.5 rounded-full bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-sm font-medium text-foreground transition-colors cursor-pointer"
                    >
                      Add Follow-up
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-44 p-2 rounded-2xl border border-border/40 shadow-xl bg-background">
                    <div className="flex flex-col gap-1">
                      {[
                        { id: "Tomorrow", label: "Tomorrow" },
                        { id: "In 3 days", label: "In 3 days" },
                        { id: "Next week", label: "Next week" },
                        { id: "In 2 weeks", label: "In 2 weeks" },
                      ].map((opt) => (
                        <DropdownMenuItem
                          key={opt.id}
                          onClick={() => handleBulkFollowUp(opt.id)}
                          className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] transition-colors outline-none hover:bg-accent/60 text-foreground"
                        >
                          {opt.label}
                        </DropdownMenuItem>
                      ))}
                    </div>
                  </DropdownMenuContent>
                </DropdownMenu>

                {/* Add Reminder Dropdown */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button 
                      type="button"
                      className="h-9 px-3.5 rounded-full bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-sm font-medium text-foreground transition-colors cursor-pointer"
                    >
                      Add Reminder
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-44 p-2 rounded-2xl border border-border/40 shadow-xl bg-background">
                    <div className="flex flex-col gap-1">
                      {[
                        { id: "In 1 hour", label: "In 1 hour" },
                        { id: "Today, 5 PM", label: "Today, 5 PM" },
                        { id: "Tomorrow morning", label: "Tomorrow morning" },
                        { id: "Next Monday", label: "Next Monday" },
                      ].map((opt) => (
                        <DropdownMenuItem
                          key={opt.id}
                          onClick={() => handleBulkReminder(opt.id)}
                          className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] transition-colors outline-none hover:bg-accent/60 text-foreground"
                        >
                          {opt.label}
                        </DropdownMenuItem>
                      ))}
                    </div>
                  </DropdownMenuContent>
                </DropdownMenu>

                {/* Delete Button */}
                <button 
                  type="button"
                  onClick={handleDeleteSelected}
                  className="h-9 px-3.5 rounded-full border border-rose-400 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 text-sm font-medium transition-colors cursor-pointer"
                >
                  Delete
                </button>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-neutral-500 font-normal">
                  {selectedLeads.size} selected
                </span>
                <button
                  type="button"
                  onClick={clearSelection}
                  className="flex items-center justify-center size-7 rounded-full hover:bg-neutral-100 dark:hover:bg-neutral-800 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                  title="Clear selection"
                >
                  <X size={20} />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Main Table / List Container */}
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
                  aria-label="Select all visible leads"
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
                No leads found.
              </div>
            ) : (
              filteredItems.map((lead, idx) => {
                const isSelected = selectedLeads.has(lead.id)
                const prevSelected = idx > 0 && selectedLeads.has(filteredItems[idx - 1].id)
                const nextSelected = idx < filteredItems.length - 1 && selectedLeads.has(filteredItems[idx + 1].id)

                let selectionRounding = "rounded-xl"
                if (isSelected) {
                  if (!prevSelected && nextSelected) {
                    selectionRounding = "rounded-t-xl border-b border-neutral-200/50 dark:border-neutral-700/40"
                  } else if (prevSelected && nextSelected) {
                    selectionRounding = "rounded-none border-b border-neutral-200/50 dark:border-neutral-700/40"
                  } else if (prevSelected && !nextSelected) {
                    selectionRounding = "rounded-b-xl"
                  } else {
                    selectionRounding = "rounded-xl"
                  }
                }

                return (
                  <div 
                    key={lead.id}
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
                          onCheckedChange={() => toggleLead(lead.id)}
                          aria-label={`Select ${lead.business_name}`}
                        />
                      </div>
                    </div>

                    {/* Main Row Content Capsule */}
                    <div 
                      onClick={() => toggleLead(lead.id)}
                      className={`flex-1 grid grid-cols-[minmax(180px,2fr)_minmax(140px,1.4fr)_minmax(140px,1.3fr)_minmax(140px,1.3fr)_minmax(170px,1.5fr)_minmax(90px,0.9fr)_minmax(80px,0.8fr)] gap-4 px-3 py-3 text-sm items-center transition-colors cursor-pointer ${
                        isSelected 
                          ? `bg-neutral-100/90 dark:bg-neutral-800/80 ${selectionRounding}` 
                          : "hover:bg-neutral-100/50 dark:hover:bg-neutral-800/40 rounded-xl"
                      }`}
                    >
                      {/* 1. Business */}
                      <div className="flex items-center min-w-0">
                        <Link 
                          href={`/business/${lead.id}`}
                          onClick={(e) => e.stopPropagation()} 
                          className="font-medium text-foreground hover:text-primary transition-colors truncate"
                          title={lead.business_name}
                        >
                          {lead.business_name}
                        </Link>
                      </div>

                      {/* 2. Location */}
                      <div className="text-muted-foreground text-xs truncate" title={lead.location || "—"}>
                        {lead.location || "—"}
                      </div>

                      {/* 3. Website */}
                      <div className="min-w-0">
                        {lead.website ? (
                          <a
                            href={lead.website.startsWith("http") ? lead.website : `https://${lead.website}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleAction(lead, "website", lead.website!)
                            }}
                            className="inline-flex items-center text-xs text-muted-foreground hover:text-foreground hover:underline truncate transition-colors max-w-full group/link py-1 px-1.5 -ml-1.5 rounded-lg hover:bg-accent/50"
                            title={`Open ${lead.website}`}
                          >
                            <span className="truncate">{lead.website.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')}</span>
                          </a>
                        ) : (
                          <span className="text-xs text-muted-foreground/40">—</span>
                        )}
                      </div>

                      {/* 4. Phone */}
                      <div className="min-w-0">
                        {lead.phone ? (
                          <a
                            href={`tel:${lead.phone}`}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleAction(lead, "call", lead.phone!)
                            }}
                            className="inline-flex items-center text-xs text-muted-foreground hover:text-foreground hover:underline truncate transition-colors max-w-full group/phone py-1 px-1.5 -ml-1.5 rounded-lg hover:bg-accent/50"
                            title={`Call ${lead.phone}`}
                          >
                            <span className="truncate">{lead.phone}</span>
                          </a>
                        ) : (
                          <span className="text-xs text-muted-foreground/40">—</span>
                        )}
                      </div>

                      {/* 5. Email */}
                      <div className="min-w-0">
                        {lead.email ? (
                          <a
                            href={`mailto:${lead.email}`}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleAction(lead, "email", lead.email!)
                            }}
                            className="inline-flex items-center text-xs text-muted-foreground hover:text-foreground hover:underline truncate transition-colors max-w-full group/email py-1 px-1.5 -ml-1.5 rounded-lg hover:bg-accent/50"
                            title={`Email ${lead.email}`}
                          >
                            <span className="truncate">{lead.email}</span>
                          </a>
                        ) : (
                          <span className="text-xs text-muted-foreground/40">—</span>
                        )}
                      </div>

                      {/* 6. WhatsApp */}
                      <div className="min-w-0">
                        {(lead.whatsapp || lead.phone) ? (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              const targetNumber = (lead.whatsapp || lead.phone || "").replace(/[^0-9]/g, "")
                              window.open(`https://wa.me/${targetNumber}`, "_blank", "noopener,noreferrer")
                              handleAction(lead, "whatsapp", lead.whatsapp || lead.phone!)
                            }}
                            className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/20 active:scale-95 transition-all cursor-pointer"
                            title={`Chat on WhatsApp (${lead.whatsapp || lead.phone})`}
                          >
                            <span>Chat</span>
                          </button>
                        ) : (
                          <span className="text-xs text-muted-foreground/40">—</span>
                        )}
                      </div>

                      {/* 7. Added */}
                      <div className="text-xs text-muted-foreground text-right truncate">
                        {new Date(lead.created_at).toLocaleDateString(undefined, {
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
