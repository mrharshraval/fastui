"use client"

import * as React from "react"
import { Plus, Search, X, Menu, MoreHorizontal } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Checkbox } from "@/components/ui/checkbox"
import { useSidebar } from "@/components/ui/sidebar"
import { api } from "@/lib/api"
import {
 DropdownMenu,
 DropdownMenuItem,
 DropdownMenuContent,
 DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface Company {
 id: string
 name: string
 domain?: string
 industry?: string
 status?: string
 leads_count?: number
}

export default function CompaniesPage() {
 const { toggleSidebar } = useSidebar()
 const [companies, setCompanies] = React.useState<Company[]>([])
 const [loading, setLoading] = React.useState(true)
 const [search, setSearch] = React.useState("")
 const [selectedCompanies, setSelectedCompanies] = React.useState<Set<string>>(new Set())

 React.useEffect(() => {
 api.get<Company[]>("/businesses")
 .then((data) => {
 if (Array.isArray(data)) {
 setCompanies(data)
 } else {
 setCompanies([])
 }
 })
 .catch(() => setCompanies([]))
 .finally(() => setLoading(false))
 }, [])

 const filtered = companies.filter((c) =>
 c.name.toLowerCase().includes(search.toLowerCase()) ||
 (c.industry ?? "").toLowerCase().includes(search.toLowerCase()) ||
 (c.domain ?? "").toLowerCase().includes(search.toLowerCase())
 )

 const isSelectionMode = selectedCompanies.size> 0
 const isAllVisibleSelected = filtered.length> 0 && filtered.every(c => selectedCompanies.has(c.id))
 const isSomeVisibleSelected = filtered.some(c => selectedCompanies.has(c.id)) && !isAllVisibleSelected

 const toggleAllVisible = () => {
 if (isAllVisibleSelected) {
 const newSelected = new Set(selectedCompanies)
 filtered.forEach(c => newSelected.delete(c.id))
 setSelectedCompanies(newSelected)
 } else {
 const newSelected = new Set(selectedCompanies)
 filtered.forEach(c => newSelected.add(c.id))
 setSelectedCompanies(newSelected)
 }
 }

 const toggleItem = (id: string) => {
 const newSelected = new Set(selectedCompanies)
 if (newSelected.has(id)) {
 newSelected.delete(id)
 } else {
 newSelected.add(id)
 }
 setSelectedCompanies(newSelected)
 }

 const clearSelection = () => {
 setSelectedCompanies(new Set())
 }

 const handleDeleteSelected = () => {
 setCompanies(companies.filter(c => !selectedCompanies.has(c.id)))
 setSelectedCompanies(new Set())
 }

 const handleSingleDelete = (id: string) => {
 setCompanies(companies.filter(c => c.id !== id))
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
 <h1 className="text-xl font-bold tracking-tight text-foreground">Companies</h1>
 </div>

 <button
 type="button"
 title="Add Company"
 className="flex items-center justify-center size-9 rounded-full bg-[#007AFF] text-white hover:bg-[#0055CC] active:scale-95 transition-all cursor-pointer shadow-xs shrink-0"
>
 <Plus size={18} strokeWidth={2.25} />
 </button>
 </div>

 {/* 2. Search Bar (Normal flow, passes underneath header, z-0) */}
 <div className="relative z-0 px-4 pt-2 pb-4 bg-background border-b border-border/30">
 <div className="relative w-full group/search">
 <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors" />
 <input
 type="text"
 placeholder="Search companies…"
 value={search}
 onChange={(e) => setSearch(e.target.value)}
 className="h-10 w-full pl-10 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
 />
 </div>
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
 ) : filtered.length === 0 ? (
 <div className="py-20 text-center text-sm text-muted-foreground">
 No companies found.
 </div>
 ) : (
 filtered.map((c) => (
 <div
 key={c.id}
 className="flex items-start justify-between py-3.5 px-4 active:bg-accent/40 transition-colors"
>
 <div className="flex flex-col min-w-0 pr-3 flex-1">
  {/* Line 1: Company Name */}
  <div className="font-semibold text-[15px] text-foreground truncate leading-tight">
  {c.name}
  </div>
  {/* Line 2: Industry */}
  <div className="text-xs text-muted-foreground truncate mt-1">
  {c.industry || "General Industry"}
  </div>
  {/* Line 3: Domain / Leads Count */}
  <div className="text-xs text-muted-foreground truncate mt-0.5">
  {c.domain ?? "—"} • {c.leads_count ?? 0} leads
  </div>
 </div>

 {/* Far Right ⋯ Action */}
 <div className="shrink-0 flex items-center justify-center">
  <DropdownMenu>
  <DropdownMenuTrigger asChild>
  <button
  type="button"
  aria-label="Company options"
  className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer shrink-0"
>
  <MoreHorizontal size={18} />
  </button>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="end" className="w-44 p-2 rounded-2xl border border-border/40 shadow-xl bg-background">
  <DropdownMenuItem
  onClick={() => handleSingleDelete(c.id)}
  className="flex items-center min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30"
>
  Delete Company
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
 DESKTOP VIEW (Full desktop table layout with guide lines)
 Visible on screen>= md
 ───────────────────────────────────────────────────────────── */}
 <div className="hidden md:flex flex-col gap-8 px-8 lg:px-12 xl:px-16 pt-14 pb-8 max-w-[1600px] w-full mx-auto">
 {/* Top Header Row - matching Home & Leads exactly */}
 <div className="flex items-center justify-between mb-2">
 <h2 className="text-xl font-bold tracking-tight text-foreground">Companies</h2>
 <div className="flex items-center gap-3">
 {/* Search Input */}
 <div className="relative group/search">
 <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors" />
 <input
 type="text"
 placeholder="Search companies..."
 value={search}
 onChange={(e) => setSearch(e.target.value)}
 className="h-9 w-44 sm:w-56 pl-9 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
 />
 </div>

 <button
 type="button"
 title="Add Company"
 className="flex items-center justify-center size-9 rounded-full bg-[#007AFF] text-white hover:bg-[#0055CC] active:scale-95 transition-all cursor-pointer shadow-xs shrink-0"
 >
 <Plus size={18} strokeWidth={2.25} />
 </button>
 </div>
 </div>

 {/* Secondary Toolbar (Search or Bulk Actions) */}
 <div className="flex items-center justify-between min-h-9">
 {!isSelectionMode ? (
 <div className="flex items-center justify-between w-full">
 <div className="text-sm text-muted-foreground font-medium">
 {companies.length} Companies
 </div>
 </div>
 ) : (
 <div className="flex items-center justify-between w-full animate-in fade-in duration-150">
 <div className="flex items-center gap-2">
 <button 
  type="button"
  onClick={handleDeleteSelected}
  className="h-9 px-4 rounded-full border border-rose-400 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 text-sm font-medium transition-colors cursor-pointer"
>
  Delete
 </button>
 </div>
 <div className="flex items-center gap-3">
 <span className="text-sm text-neutral-500 font-normal">
  {selectedCompanies.size} selected
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

 {/* Main List Container */}
 <div className="flex flex-col -ml-12 w-[calc(100%+3rem)]">
 {/* Header Row */}
 <div className="flex items-center group/header w-full pb-2.5 select-none">
 <div className="w-9 shrink-0 flex items-center justify-center">
 <div 
 className={`transition-opacity duration-150 ${
  isSelectionMode ? "opacity-100" : "opacity-0 group-hover/header:opacity-100 hover:opacity-100"
 }`}
>
 <Checkbox 
  checked={isAllVisibleSelected ? true : isSomeVisibleSelected ? 'indeterminate' : false}
  onCheckedChange={toggleAllVisible}
  aria-label="Select all visible companies"
 />
 </div>
 </div>

 <div className="flex-1 grid grid-cols-12 gap-4 px-3 text-[14px] font-medium text-muted-foreground items-center">
 <div className="col-span-4">Company</div>
 <div className="col-span-3">Domain</div>
 <div className="col-span-3">Industry</div>
 <div className="col-span-2 text-right">Leads</div>
 </div>
 </div>

 {/* Rows */}
 <div className="flex flex-col w-full">
 {loading ? (
 Array.from({ length: 5 }).map((_, i) => (
 <div key={i} className="flex items-center w-full py-2.5">
  <div className="w-9 shrink-0 flex items-center justify-center">
  <Skeleton className="size-4 rounded" />
  </div>
  <div className="flex-1 grid grid-cols-12 gap-4 px-3 items-center">
  <Skeleton className="col-span-4 h-4 rounded" />
  <Skeleton className="col-span-3 h-4 rounded" />
  <Skeleton className="col-span-3 h-4 rounded" />
  <Skeleton className="col-span-2 h-4 rounded" />
  </div>
 </div>
 ))
 ) : filtered.length === 0 ? (
 <div className="py-16 text-center text-sm text-muted-foreground">
 No companies found.
 </div>
 ) : (
 filtered.map((c, idx) => {
 const isSelected = selectedCompanies.has(c.id)
 const prevSelected = idx> 0 && selectedCompanies.has(filtered[idx - 1].id)
 const nextSelected = idx < filtered.length - 1 && selectedCompanies.has(filtered[idx + 1].id)

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
  <div key={c.id} className="flex items-center group/row w-full my-[1px] relative">
  <div className="w-9 shrink-0 flex items-center justify-center">
  <div 
  className={`transition-opacity duration-150 ${
  isSelected ? "opacity-100" : "opacity-0 group-hover/row:opacity-100 hover:opacity-100"
  }`}
  onClick={(e) => e.stopPropagation()}
>
  <Checkbox 
  checked={isSelected}
  onCheckedChange={() => toggleItem(c.id)}
  aria-label={`Select ${c.name}`}
  />
  </div>
  </div>

  <div 
  onClick={() => toggleItem(c.id)}
  className={`flex-1 grid grid-cols-12 gap-4 px-3 py-3 text-sm items-center transition-colors cursor-pointer ${
  isSelected 
  ? `bg-neutral-100/90 dark:bg-neutral-800/80 ${selectionRounding}` 
  : "hover:bg-neutral-100/50 dark:hover:bg-neutral-800/40 rounded-xl"
  }`}
>
  <div className="col-span-4 font-medium text-foreground truncate">
  {c.name}
  </div>
  <div className="col-span-3 text-muted-foreground text-xs truncate">
  {c.domain ?? "—"}
  </div>
  <div className="col-span-3 text-muted-foreground text-xs truncate">
  {c.industry ?? "—"}
  </div>
  <div className="col-span-2 flex justify-end">
  <Badge variant="secondary" className="text-xs rounded-full px-2.5 py-0.5 font-normal">
  {c.leads_count ?? 0} leads
  </Badge>
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
