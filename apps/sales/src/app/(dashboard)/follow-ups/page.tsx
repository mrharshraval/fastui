"use client"

import * as React from "react"
import { 
  Search, Plus, CheckCircle2, ListFilter, 
  Clock, AlertCircle, Check, X, Menu, MoreHorizontal 
} from "lucide-react"
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

interface FollowUp { 
  id: string
  lead_name?: string
  note?: string
  due_date?: string
  status: string 
}

const STATUS_COLOR: Record<string, "default" | "secondary" | "outline" | "destructive"> = { 
  pending: "secondary", 
  done: "default", 
  overdue: "destructive" 
}

export default function FollowUpsPage() {
  const { toggleSidebar } = useSidebar()
  const [items, setItems] = React.useState<FollowUp[]>([])
  const [loading, setLoading] = React.useState(true)
  const [searchQuery, setSearchQuery] = React.useState("")
  const [statusFilter, setStatusFilter] = React.useState("all")
  const [selectedItems, setSelectedItems] = React.useState<Set<string>>(new Set())

  React.useEffect(() => { 
    api.get<FollowUp[]>("/follow-ups")
      .then((data) => {
        if (Array.isArray(data)) {
          setItems(data)
        } else {
          setItems([])
        }
      })
      .catch(() => setItems([]))
      .finally(() => setLoading(false)) 
  }, [])

  const filteredItems = items.filter((f) => {
    const matchesSearch = !searchQuery || 
      f.lead_name?.toLowerCase().includes(searchQuery.toLowerCase()) || 
      f.note?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || f.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const isSelectionMode = selectedItems.size > 0
  const isAllVisibleSelected = filteredItems.length > 0 && filteredItems.every(f => selectedItems.has(f.id))
  const isSomeVisibleSelected = filteredItems.some(f => selectedItems.has(f.id)) && !isAllVisibleSelected

  const toggleAllVisible = () => {
    if (isAllVisibleSelected) {
      const newSelected = new Set(selectedItems)
      filteredItems.forEach(f => newSelected.delete(f.id))
      setSelectedItems(newSelected)
    } else {
      const newSelected = new Set(selectedItems)
      filteredItems.forEach(f => newSelected.add(f.id))
      setSelectedItems(newSelected)
    }
  }

  const toggleItem = (id: string) => {
    const newSelected = new Set(selectedItems)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedItems(newSelected)
  }

  const clearSelection = () => {
    setSelectedItems(new Set())
  }

  const handleDeleteSelected = () => {
    setItems(items.filter(f => !selectedItems.has(f.id)))
    setSelectedItems(new Set())
  }

  const handleSingleDelete = (id: string) => {
    setItems(items.filter(f => f.id !== id))
  }

  const filterDropdownMenu = (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="Filter"
          className="relative flex items-center justify-center size-9 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-colors cursor-pointer shrink-0"
        >
          <ListFilter size={18} />
          {statusFilter !== "all" && (
            <span className="absolute -top-0.5 -right-0.5 size-4 rounded-full bg-neutral-900 text-white dark:bg-white dark:text-black text-[10px] flex items-center justify-center font-bold shadow-sm pointer-events-none">
              1
            </span>
          )}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent 
        align="end" 
        className="w-52 p-2 rounded-3xl border border-border/40 shadow-xl bg-background"
      >
        <div className="flex items-center justify-between px-3 py-1.5 border-b border-border/40 mb-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Filter</span>
          {statusFilter !== "all" && (
            <button
              onClick={() => setStatusFilter("all")}
              className="text-xs text-primary font-medium hover:underline cursor-pointer"
            >
              Reset
            </button>
          )}
        </div>
        <div className="flex flex-col gap-1">
          {[
            { id: "all", label: "All Statuses", icon: <ListFilter size={20} className="shrink-0" /> },
            { id: "pending", label: "Pending", icon: <Clock size={20} className="shrink-0" /> },
            { id: "done", label: "Done", icon: <CheckCircle2 size={20} className="shrink-0" /> },
            { id: "overdue", label: "Overdue", icon: <AlertCircle size={20} className="shrink-0" /> },
          ].map((s) => (
            <DropdownMenuItem
              key={s.id}
              onClick={() => setStatusFilter(s.id)}
              className="flex items-center justify-between min-h-9 px-2.5 rounded-2xl cursor-pointer text-[14px] font-[500] hover:bg-accent/60 text-foreground"
            >
              <div className="flex items-center gap-2.5">
                {s.icon}
                {s.label}
              </div>
              {statusFilter === s.id && <Check size={20} className="shrink-0" />}
            </DropdownMenuItem>
          ))}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )

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
            <h1 className="text-xl font-bold tracking-tight text-foreground">Follow-ups</h1>
          </div>

          <button
            type="button"
            title="Add Follow-up"
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
              placeholder="Search follow-ups…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-10 w-full pl-10 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
            />
          </div>
        </div>

        {/* 3. Sticky Filter Bar (Scrolls up to top, locks stickily overlapping header, z-30) */}
        <div className="sticky top-0 z-30 bg-background/95 backdrop-blur-md px-4 py-2 border-b border-border/30 flex items-center justify-between gap-2 shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 min-w-0 flex-1">
            {["all", "pending", "overdue", "done"].map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setStatusFilter(tab)}
                className={`h-9 px-3.5 rounded-full text-sm capitalize transition-colors cursor-pointer shrink-0 whitespace-nowrap ${
                  statusFilter === tab
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
          ) : filteredItems.length === 0 ? (
            <div className="py-20 text-center text-sm text-muted-foreground">
              No follow-ups found.
            </div>
          ) : (
            filteredItems.map((f) => (
              <div
                key={f.id}
                className="flex items-start justify-between py-3.5 px-4 active:bg-accent/40 transition-colors"
              >
                <div className="flex flex-col min-w-0 pr-3 flex-1">
                  {/* Line 1: Lead Name */}
                  <div className="font-semibold text-[15px] text-foreground truncate leading-tight">
                    {f.lead_name || "Follow-up Task"}
                  </div>
                  {/* Line 2: Note */}
                  <div className="text-xs text-muted-foreground truncate mt-1">
                    {f.note || "No details provided"}
                  </div>
                  {/* Line 3: Due Date & Status */}
                  <div className="text-xs text-muted-foreground truncate mt-0.5">
                    {f.due_date || "No due date"} • {f.status}
                  </div>
                </div>

                {/* Far Right ⋯ Action */}
                <div className="shrink-0 flex items-center justify-center">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button
                        type="button"
                        aria-label="Follow-up options"
                        className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer shrink-0"
                      >
                        <MoreHorizontal size={18} />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-44 p-2 rounded-2xl border border-border/40 shadow-xl bg-background">
                      <DropdownMenuItem
                        onClick={() => handleSingleDelete(f.id)}
                        className="flex items-center min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30"
                      >
                        Delete Follow-up
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
          Visible on screen >= md
         ───────────────────────────────────────────────────────────── */}
      <div className="hidden md:flex flex-col gap-8 px-8 lg:px-12 xl:px-16 pt-14 pb-8 max-w-[1600px] w-full mx-auto">
        {/* Top Header Row - matching Home & Leads exactly */}
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold tracking-tight text-foreground">Follow-ups</h2>
          <div className="flex items-center gap-3">
            <div className="relative group/search">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors" />
              <input
                type="text"
                placeholder="Search follow-ups..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-9 w-44 sm:w-56 pl-9 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
              />
            </div>
            
            <button
              type="button"
              title="Add Follow-up"
              className="flex items-center justify-center size-9 rounded-full bg-[#007AFF] text-white hover:bg-[#0055CC] active:scale-95 transition-all cursor-pointer shadow-xs shrink-0"
            >
              <Plus size={18} strokeWidth={2.25} />
            </button>
          </div>
        </div>

        {/* Secondary Toolbar (Tabs & Search or Contextual Actions) */}
        <div className="flex items-center justify-between min-h-9">
          {!isSelectionMode ? (
            <>
              <div className="flex items-center gap-1.5">
                {["all", "pending", "overdue", "done"].map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setStatusFilter(tab)}
                    className={`h-9 px-3.5 rounded-full text-sm capitalize transition-colors cursor-pointer ${
                      statusFilter === tab
                        ? "bg-neutral-100 dark:bg-neutral-800 text-foreground font-semibold"
                        : "text-muted-foreground hover:text-foreground font-medium"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              <div className="flex items-center">
                {filterDropdownMenu}
              </div>
            </>
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
                  {selectedItems.size} selected
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
          {/* Table Header Row */}
          <div className="flex items-center group/header w-full pb-2.5 select-none min-w-[700px]">
            <div className="w-9 shrink-0 flex items-center justify-center">
              <div 
                className={`transition-opacity duration-150 ${
                  isSelectionMode ? "opacity-100" : "opacity-0 group-hover/header:opacity-100 hover:opacity-100"
                }`}
              >
                <Checkbox 
                  checked={isAllVisibleSelected ? true : isSomeVisibleSelected ? 'indeterminate' : false}
                  onCheckedChange={toggleAllVisible}
                  aria-label="Select all visible follow-ups"
                />
              </div>
            </div>

            <div className="flex-1 grid grid-cols-12 gap-4 px-3 text-[14px] font-medium text-muted-foreground items-center">
              <div className="col-span-4">Lead</div>
              <div className="col-span-4">Note</div>
              <div className="col-span-2">Due Date</div>
              <div className="col-span-2 text-right">Status</div>
            </div>
          </div>

          {/* Table Body Rows */}
          <div className="flex flex-col w-full min-w-[700px]">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center w-full py-2.5">
                  <div className="w-9 shrink-0 flex items-center justify-center">
                    <Skeleton className="size-4 rounded" />
                  </div>
                  <div className="flex-1 grid grid-cols-12 gap-4 px-3 items-center">
                    <Skeleton className="col-span-4 h-4 rounded" />
                    <Skeleton className="col-span-4 h-4 rounded" />
                    <Skeleton className="col-span-2 h-4 rounded" />
                    <Skeleton className="col-span-2 h-4 rounded" />
                  </div>
                </div>
              ))
            ) : filteredItems.length === 0 ? (
              <div className="py-16 text-center text-sm text-muted-foreground">
                No follow-ups found.
              </div>
            ) : (
              filteredItems.map((f, idx) => {
                const isSelected = selectedItems.has(f.id)
                const prevSelected = idx > 0 && selectedItems.has(filteredItems[idx - 1].id)
                const nextSelected = idx < filteredItems.length - 1 && selectedItems.has(filteredItems[idx + 1].id)

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
                  <div key={f.id} className="flex items-center group/row w-full my-[1px] relative">
                    <div className="w-9 shrink-0 flex items-center justify-center">
                      <div 
                        className={`transition-opacity duration-150 ${
                          isSelected ? "opacity-100" : "opacity-0 group-hover/row:opacity-100 hover:opacity-100"
                        }`}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Checkbox 
                          checked={isSelected}
                          onCheckedChange={() => toggleItem(f.id)}
                          aria-label={`Select ${f.lead_name}`}
                        />
                      </div>
                    </div>

                    <div 
                      onClick={() => toggleItem(f.id)}
                      className={`flex-1 grid grid-cols-12 gap-4 px-3 py-3 text-sm items-center transition-colors cursor-pointer ${
                        isSelected 
                          ? `bg-neutral-100/90 dark:bg-neutral-800/80 ${selectionRounding}` 
                          : "hover:bg-neutral-100/50 dark:hover:bg-neutral-800/40 rounded-xl"
                      }`}
                    >
                      <div className="col-span-4 font-medium text-foreground truncate">
                        {f.lead_name}
                      </div>
                      <div className="col-span-4 text-muted-foreground text-xs truncate">
                        {f.note}
                      </div>
                      <div className="col-span-2 text-muted-foreground text-xs truncate">
                        {f.due_date}
                      </div>
                      <div className="col-span-2 flex justify-end">
                        <Badge variant={STATUS_COLOR[f.status] ?? "secondary"} className="text-xs rounded-full px-2.5 py-0.5 capitalize font-normal">
                          {f.status}
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
