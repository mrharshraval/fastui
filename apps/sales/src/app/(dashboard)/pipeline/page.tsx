"use client"

import * as React from "react"
import { Plus, Menu, MoreHorizontal, Search } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useSidebar } from "@/components/ui/sidebar"
import { api } from "@/lib/api"
import {
 DropdownMenu,
 DropdownMenuItem,
 DropdownMenuContent,
 DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const STAGES = ["Qualification", "Demo", "Proposal", "Negotiation", "Closed Won"]

interface Deal { 
 id: string
 business_name: string
 value?: number
 stage: string
 probability?: number 
}

export default function PipelinePage() {
 const { toggleSidebar } = useSidebar()
 const [deals, setDeals] = React.useState<Deal[]>([])
 const [loading, setLoading] = React.useState(true)
 const [activeStage, setActiveStage] = React.useState("all")
 const [search, setSearch] = React.useState("")

 React.useEffect(() => { 
 api.get<Deal[]>("/pipeline")
 .then((data) => {
 if (Array.isArray(data)) {
  setDeals(data)
 } else {
  setDeals([])
 }
 })
 .catch(() => setDeals([]))
 .finally(() => setLoading(false)) 
 }, [])

 const byStage = (stage: string) => deals.filter((d) => d.stage === stage)

 const filteredDeals = deals.filter((d) => {
 const matchesSearch = !search || d.business_name.toLowerCase().includes(search.toLowerCase());
 const matchesStage = activeStage === "all" || d.stage === activeStage;
 return matchesSearch && matchesStage;
 })

 const handleSingleDelete = (id: string) => {
 setDeals(deals.filter(d => d.id !== id))
 }

 return (
 <>
 {/* ─────────────────────────────────────────────────────────────
  MOBILE VIEW (Native Mobile List with Layered Sticky Header)
  Visible on screen < md (phone view)
  ───────────────────────────────────────────────────────────── */}
 <div className="flex flex-col w-full md:hidden pb-16">
 {/* 1. Mobile Header (Sticky at top, z-10) */}
 <div className="sticky top-0 z-10 bg-background flex items-center justify-between px-4 pt-4 pb-2">
  <div className="flex items-center gap-2">
  <button
  type="button"
  onClick={toggleSidebar}
  className="flex items-center justify-center size-9 -ml-1.5 rounded-full text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer"
  aria-label="Open navigation"
>
  <Menu size={20} />
  </button>
  <h1 className="text-xl font-bold tracking-tight text-foreground">Pipeline</h1>
  </div>

  <button
  type="button"
  title="Add Deal"
  className="flex items-center justify-center size-9 rounded-full bg-[#007AFF] text-white hover:bg-[#0055CC] active:scale-95 transition-all cursor-pointer shadow-xs shrink-0"
>
  <Plus size={18} strokeWidth={2.25} />
  </button>
 </div>

 {/* 2. Search Bar (Normal flow, passes underneath header, z-0) */}
 <div className="relative z-0 px-4 pt-2 pb-4 bg-background">
  <div className="relative w-full group/search">
  <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors" />
  <input
  type="text"
  placeholder="Search deals…"
  value={search}
  onChange={(e) => setSearch(e.target.value)}
  className="h-10 w-full pl-10 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
  />
  </div>
 </div>

 {/* 3. Sticky Stage Tabs (Scrolls up to top, locks stickily overlapping header, z-30) */}
 <div className="sticky top-0 z-30 bg-background/95 backdrop-blur-md px-4 py-2 border-b border-border/30 flex items-center gap-1.5 overflow-x-auto no-scrollbar shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
  <button
  type="button"
  onClick={() => setActiveStage("all")}
  className={`h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer shrink-0 whitespace-nowrap ${
  activeStage === "all"
  ? "bg-neutral-900 text-white dark:bg-white dark:text-black font-semibold shadow-sm"
  : "text-muted-foreground hover:text-foreground font-medium"
  }`}
>
  All Stages
  </button>
  {STAGES.map((st) => (
  <button
  key={st}
  type="button"
  onClick={() => setActiveStage(st)}
  className={`h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer shrink-0 whitespace-nowrap ${
  activeStage === st
   ? "bg-neutral-900 text-white dark:bg-white dark:text-black font-semibold shadow-sm"
   : "text-muted-foreground hover:text-foreground font-medium"
  }`}
>
  {st} ({byStage(st).length})
  </button>
  ))}
 </div>

 {/* Mobile List Content */}
 <div className="flex flex-col w-full divide-y divide-border/30">
  {loading ? (
  Array.from({ length: 6 }).map((_, i) => (
  <div key={i} className="flex flex-col gap-2 py-3.5 px-4">
  <Skeleton className="h-4 w-36 rounded" />
  <Skeleton className="h-3 w-28 rounded" />
  <Skeleton className="h-3 w-20 rounded" />
  </div>
  ))
  ) : filteredDeals.length === 0 ? (
  <div className="py-20 text-center text-sm text-muted-foreground">
  No deals found.
  </div>
  ) : (
  filteredDeals.map((deal) => (
  <div
  key={deal.id}
  className="flex items-start justify-between py-3.5 px-4 active:bg-accent/40 transition-colors"
>
  <div className="flex flex-col min-w-0 pr-3 flex-1">
   {/* Line 1: Deal Name */}
   <div className="font-semibold text-[15px] text-foreground truncate leading-tight">
   {deal.business_name}
   </div>
   {/* Line 2: Value & Probability */}
   <div className="text-xs text-muted-foreground truncate mt-1">
   {deal.value ? `$${deal.value.toLocaleString("en-US")}` : "No value"} {deal.probability ? `• ${deal.probability}% win probability` : ""}
   </div>
   {/* Line 3: Stage */}
   <div className="text-xs text-muted-foreground truncate mt-0.5">
   {deal.stage}
   </div>
  </div>

  {/* Far Right ⋯ Action */}
  <div className="shrink-0 flex items-center justify-center">
   <DropdownMenu>
   <DropdownMenuTrigger asChild>
   <button
   type="button"
   aria-label="Deal options"
   className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer shrink-0"
 >
   <MoreHorizontal size={18} />
   </button>
   </DropdownMenuTrigger>
   <DropdownMenuContent align="end" className="w-44 p-2 rounded-2xl border border-border/40 shadow-xl bg-background">
   <DropdownMenuItem
   onClick={() => handleSingleDelete(deal.id)}
   className="flex items-center min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30"
 >
   Delete Deal
   </DropdownMenuItem>
   </DropdownMenuContent>
   </DropdownMenu>
  </div>
  </div>
  ))
  )}
 </div>
 </div>

 {/* ─────────────────────────────────────────────────────────────
  DESKTOP VIEW (Kanban Pipeline Board)
  Visible on screen>= md
  ───────────────────────────────────────────────────────────── */}
 <div className="hidden md:flex flex-col gap-8 px-8 lg:px-12 xl:px-16 pt-14 pb-8 max-w-[1600px] w-full mx-auto">
 <div className="flex items-center justify-between mb-2">
  <h2 className="text-xl font-bold tracking-tight text-foreground">Pipeline</h2>
  <button
  type="button"
  title="Add Deal"
  className="flex items-center justify-center size-9 rounded-full bg-[#007AFF] text-white hover:bg-[#0055CC] active:scale-95 transition-all cursor-pointer shadow-xs shrink-0"
>
  <Plus size={18} strokeWidth={2.25} />
  </button>
 </div>

 {/* Kanban Board Grid */}
 <div className="flex gap-4 overflow-x-auto pb-4">
  {STAGES.map((stage) => (
  <div key={stage} className="flex flex-col gap-3 min-w-[240px] w-[240px] shrink-0">
  <div className="flex items-center justify-between px-1">
  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{stage}</span>
  <Badge variant="secondary" className="text-xs rounded-full">{byStage(stage).length}</Badge>
  </div>
  <div className="flex flex-col gap-2.5">
  {loading
   ? Array.from({length:2}).map((_,i) => <Skeleton key={i} className="h-20 rounded-xl" />)
   : byStage(stage).length === 0
   ? <div className="h-20 rounded-xl bg-accent/20 flex items-center justify-center"><span className="text-xs text-muted-foreground">No deals</span></div>
   : byStage(stage).map((deal) => (
   <Card key={deal.id} className="bg-card rounded-xl hover:shadow-md transition-shadow cursor-grab active:cursor-grabbing border-border/40">
   <CardHeader className="pb-2 pt-3.5 px-3.5">
   <CardTitle className="text-sm font-medium leading-tight">{deal.business_name}</CardTitle>
   </CardHeader>
   <CardContent className="px-3.5 pb-3.5 pt-0">
   <div className="flex items-center justify-between">
    {deal.value && <span className="text-xs font-semibold">${deal.value.toLocaleString("en-US")}</span>}
    {deal.probability && <span className="text-xs text-muted-foreground">{deal.probability}%</span>}
   </div>
   </CardContent>
   </Card>
   ))
  }
  </div>
  </div>
  ))}
 </div>
 </div>
 </>
 )
}
