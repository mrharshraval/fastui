"use client"

import * as React from "react"
import { Plus, Search, X, Menu, MoreHorizontal, Check } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
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

interface Contact {
 id: string
 name: string
 email?: string
 phone?: string
 company?: string
 role?: string
}

export default function AccountsPage() {
 const { toggleSidebar } = useSidebar()
 const [activeTab, setActiveTab] = React.useState<"companies" | "contacts">("companies")

 // Companies state
 const [companies, setCompanies] = React.useState<Company[]>([])
 const [loadingCompanies, setLoadingCompanies] = React.useState(true)

 // Contacts state
 const [contacts, setContacts] = React.useState<Contact[]>([])
 const [loadingContacts, setLoadingContacts] = React.useState(true)

 const [search, setSearch] = React.useState("")

 // Selection state
 const [selectedCompanies, setSelectedCompanies] = React.useState<Set<string>>(new Set())
 const [selectedContacts, setSelectedContacts] = React.useState<Set<string>>(new Set())

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
    .finally(() => setLoadingCompanies(false))

  api.get<Contact[]>("/contacts")
    .then((data) => {
      if (Array.isArray(data)) {
        setContacts(data)
      } else {
        setContacts([])
      }
    })
    .catch(() => setContacts([]))
    .finally(() => setLoadingContacts(false))
 }, [])

 const filteredCompanies = companies.filter((c) =>
 c.name.toLowerCase().includes(search.toLowerCase()) ||
 (c.industry ?? "").toLowerCase().includes(search.toLowerCase()) ||
 (c.domain ?? "").toLowerCase().includes(search.toLowerCase())
 )

 const filteredContacts = contacts.filter((c) =>
 c.name.toLowerCase().includes(search.toLowerCase()) ||
 (c.email ?? "").toLowerCase().includes(search.toLowerCase()) ||
 (c.company ?? "").toLowerCase().includes(search.toLowerCase()) ||
 (c.role ?? "").toLowerCase().includes(search.toLowerCase())
 )

 const currentSelection = activeTab === "companies" ? selectedCompanies : selectedContacts
 const setCurrentSelection = activeTab === "companies" ? setSelectedCompanies : setSelectedContacts
 const currentFiltered = activeTab === "companies" ? filteredCompanies : filteredContacts

 const isSelectionMode = currentSelection.size> 0
 const isAllVisibleSelected = currentFiltered.length> 0 && currentFiltered.every(item => currentSelection.has(item.id))
 const isSomeVisibleSelected = currentFiltered.some(item => currentSelection.has(item.id)) && !isAllVisibleSelected

 const toggleAllVisible = () => {
 if (isAllVisibleSelected) {
 const newSelected = new Set(currentSelection)
 currentFiltered.forEach(item => newSelected.delete(item.id))
 setCurrentSelection(newSelected)
 } else {
 const newSelected = new Set(currentSelection)
 currentFiltered.forEach(item => newSelected.add(item.id))
 setCurrentSelection(newSelected)
 }
 }

 const toggleItem = (id: string) => {
 const newSelected = new Set(currentSelection)
 if (newSelected.has(id)) {
 newSelected.delete(id)
 } else {
 newSelected.add(id)
 }
 setCurrentSelection(newSelected)
 }

 const clearSelection = () => {
 setCurrentSelection(new Set())
 }

 const handleDeleteSelected = () => {
 if (activeTab === "companies") {
 setCompanies(companies.filter(c => !selectedCompanies.has(c.id)))
 setSelectedCompanies(new Set())
 } else {
 setContacts(contacts.filter(c => !selectedContacts.has(c.id)))
 setSelectedContacts(new Set())
 }
 }

 const handleSingleDeleteCompany = (id: string) => {
 setCompanies(companies.filter(c => c.id !== id))
 }

 const handleSingleDeleteContact = (id: string) => {
 setContacts(contacts.filter(c => c.id !== id))
 }

 const initials = (name: string) =>
 name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)

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
 <h1 className="text-xl font-bold tracking-tight text-foreground">Accounts</h1>
 </div>

 <button
 type="button"
 title={activeTab === "companies" ? "Add Company" : "Add Contact"}
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
 placeholder={activeTab === "companies" ? "Search companies…" : "Search contacts…"}
 value={search}
 onChange={(e) => setSearch(e.target.value)}
 className="h-10 w-full pl-10 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
 />
 </div>
 </div>

 {/* 3. Sticky Tab Bar (Scrolls up to top, locks stickily overlapping header, z-30) */}
 <div className="sticky top-0 z-30 bg-background/95 backdrop-blur-md px-4 py-2 border-b border-border/30 flex items-center gap-1.5 shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
 <button
 type="button"
 onClick={() => { setActiveTab("companies"); setSearch("") }}
 className={`h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer shrink-0 whitespace-nowrap ${
 activeTab === "companies"
 ? "bg-neutral-900 text-white dark:bg-white dark:text-black font-semibold shadow-sm"
 : "text-muted-foreground hover:text-foreground font-medium"
 }`}
>
 Companies ({companies.length})
 </button>
 <button
 type="button"
 onClick={() => { setActiveTab("contacts"); setSearch("") }}
 className={`h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer shrink-0 whitespace-nowrap ${
 activeTab === "contacts"
 ? "bg-neutral-900 text-white dark:bg-white dark:text-black font-semibold shadow-sm"
 : "text-muted-foreground hover:text-foreground font-medium"
 }`}
>
 Contacts ({contacts.length})
 </button>
 </div>

 {/* Mobile List Content */}
 <div className="flex flex-col w-full divide-y divide-border/30">
 {activeTab === "companies" ? (
 loadingCompanies ? (
 Array.from({ length: 6 }).map((_, i) => (
 <div key={i} className="flex flex-col gap-2 py-3.5 px-4">
 <Skeleton className="h-4 w-36 rounded" />
 <Skeleton className="h-3 w-28 rounded" />
 <Skeleton className="h-3 w-20 rounded" />
 </div>
 ))
 ) : filteredCompanies.length === 0 ? (
 <div className="py-20 text-center text-sm text-muted-foreground">
 No companies found.
 </div>
 ) : (
 filteredCompanies.map((c) => (
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
 onClick={() => handleSingleDeleteCompany(c.id)}
 className="flex items-center min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30"
>
 Delete Company
 </DropdownMenuItem>
 </DropdownMenuContent>
 </DropdownMenu>
 </div>
 </div>
 ))
 )
 ) : (
 loadingContacts ? (
 Array.from({ length: 6 }).map((_, i) => (
 <div key={i} className="flex flex-col gap-2 py-3.5 px-4">
 <Skeleton className="h-4 w-36 rounded" />
 <Skeleton className="h-3 w-28 rounded" />
 <Skeleton className="h-3 w-20 rounded" />
 </div>
 ))
 ) : filteredContacts.length === 0 ? (
 <div className="py-20 text-center text-sm text-muted-foreground">
 No contacts found.
 </div>
 ) : (
 filteredContacts.map((c) => (
 <div
 key={c.id}
 className="flex items-start justify-between py-3.5 px-4 active:bg-accent/40 transition-colors"
>
 <div className="flex flex-col min-w-0 pr-3 flex-1">
 {/* Line 1: Contact Name */}
 <div className="flex items-center gap-2 font-semibold text-[15px] text-foreground truncate leading-tight">
 <Avatar className="size-5 rounded-full shrink-0">
 <AvatarFallback className="text-[10px] font-semibold bg-accent text-foreground rounded-full">
 {initials(c.name)}
 </AvatarFallback>
 </Avatar>
 <span className="truncate">{c.name}</span>
 </div>
 {/* Line 2: Company & Role */}
 <div className="text-xs text-muted-foreground truncate mt-1">
 {c.company ?? "—"} {c.role ? `• ${c.role}` : ""}
 </div>
 {/* Line 3: Email */}
 <div className="text-xs text-muted-foreground truncate mt-0.5">
 {c.email ?? "—"}
 </div>
 </div>

 {/* Far Right ⋯ Action */}
 <div className="shrink-0 flex items-center justify-center">
 <DropdownMenu>
 <DropdownMenuTrigger asChild>
 <button
 type="button"
 aria-label="Contact options"
 className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer shrink-0"
>
 <MoreHorizontal size={18} />
 </button>
 </DropdownMenuTrigger>
 <DropdownMenuContent align="end" className="w-44 p-2 rounded-2xl border border-border/40 shadow-xl bg-background">
 <DropdownMenuItem
 onClick={() => handleSingleDeleteContact(c.id)}
 className="flex items-center min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30"
>
 Delete Contact
 </DropdownMenuItem>
 </DropdownMenuContent>
 </DropdownMenu>
 </div>
 </div>
 ))
 )
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
 <h2 className="text-xl font-bold tracking-tight text-foreground">Accounts</h2>
 <div className="flex items-center gap-3">
 {/* Search Input */}
 <div className="relative group/search">
 <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors" />
 <input
 type="text"
 placeholder={activeTab === "companies" ? "Search companies..." : "Search contacts..."}
 value={search}
 onChange={(e) => setSearch(e.target.value)}
 className="h-9 w-44 sm:w-56 pl-9 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
 />
 </div>

 <button
 type="button"
 title={activeTab === "companies" ? "Add Company" : "Add Contact"}
 className="flex items-center justify-center size-9 rounded-full bg-[#007AFF] text-white hover:bg-[#0055CC] active:scale-95 transition-all cursor-pointer shadow-xs shrink-0"
>
 <Plus size={18} strokeWidth={2.25} />
 </button>
 </div>
 </div>

 {/* Secondary Toolbar (Tabs & Search or Contextual Actions) */}
 <div className="flex items-center justify-between min-h-9">
 {!isSelectionMode ? (
 <div className="flex items-center gap-1.5">
 <button
 type="button"
 onClick={() => { setActiveTab("companies"); setSearch("") }}
 className={`h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer ${
 activeTab === "companies"
 ? "bg-neutral-100 dark:bg-neutral-800 text-foreground font-semibold"
 : "text-muted-foreground hover:text-foreground font-medium"
 }`}
>
 Companies ({companies.length})
 </button>
 <button
 type="button"
 onClick={() => { setActiveTab("contacts"); setSearch("") }}
 className={`h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer ${
 activeTab === "contacts"
 ? "bg-neutral-100 dark:bg-neutral-800 text-foreground font-semibold"
 : "text-muted-foreground hover:text-foreground font-medium"
 }`}
>
 Contacts ({contacts.length})
 </button>
 </div>
 ) : (
 <div className="flex items-center justify-between w-full animate-in fade-in duration-150">
 <div className="flex items-center gap-2">
 <button 
 type="button"
 className="h-9 px-4 rounded-full bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-sm font-medium text-foreground transition-colors cursor-pointer"
>
 Assign
 </button>
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
 {currentSelection.size} selected
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
 {/* VIEW: Companies */}
 {activeTab === "companies" && (
 <>
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
 {loadingCompanies ? (
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
 ) : filteredCompanies.length === 0 ? (
 <div className="py-16 text-center text-sm text-muted-foreground">
 No companies found.
 </div>
 ) : (
 filteredCompanies.map((c, idx) => {
 const isSelected = selectedCompanies.has(c.id)
 const prevSelected = idx> 0 && selectedCompanies.has(filteredCompanies[idx - 1].id)
 const nextSelected = idx < filteredCompanies.length - 1 && selectedCompanies.has(filteredCompanies[idx + 1].id)

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
 </>
 )}

 {/* VIEW: Contacts */}
 {activeTab === "contacts" && (
 <>
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
 aria-label="Select all visible contacts"
 />
 </div>
 </div>

 <div className="flex-1 grid grid-cols-12 gap-4 px-3 text-[14px] font-medium text-muted-foreground items-center">
 <div className="col-span-4">Contact</div>
 <div className="col-span-3">Email</div>
 <div className="col-span-3">Company</div>
 <div className="col-span-2 text-right">Role</div>
 </div>
 </div>

 {/* Rows */}
 <div className="flex flex-col w-full">
 {loadingContacts ? (
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
 ) : filteredContacts.length === 0 ? (
 <div className="py-16 text-center text-sm text-muted-foreground">
 No contacts found.
 </div>
 ) : (
 filteredContacts.map((c, idx) => {
 const isSelected = selectedContacts.has(c.id)
 const prevSelected = idx> 0 && selectedContacts.has(filteredContacts[idx - 1].id)
 const nextSelected = idx < filteredContacts.length - 1 && selectedContacts.has(filteredContacts[idx + 1].id)

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
 <div className="col-span-4 flex items-center gap-2.5 truncate">
 <Avatar className="size-7 rounded-full shrink-0">
 <AvatarFallback className="text-[11px] font-semibold bg-accent text-foreground rounded-full">
 {initials(c.name)}
 </AvatarFallback>
 </Avatar>
 <span className="font-medium text-foreground truncate">{c.name}</span>
 </div>
 <div className="col-span-3 text-muted-foreground text-xs truncate">
 {c.email ?? "—"}
 </div>
 <div className="col-span-3 text-muted-foreground text-xs truncate">
 {c.company ?? "—"}
 </div>
 <div className="col-span-2 text-muted-foreground text-xs text-right truncate">
 {c.role ?? "—"}
 </div>
 </div>
 </div>
 )
 })
 )}
 </div>
 </>
 )}
 </div>
 </div>
 </>
 )
}
