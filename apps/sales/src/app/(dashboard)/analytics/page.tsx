"use client"

import * as React from "react"
import { BarChart3, Plus, Menu } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { useSidebar } from "@/components/ui/sidebar"

export default function AnalyticsPage() {
 const { toggleSidebar } = useSidebar()

 return (
 <>
 {/* Mobile Sticky Header */}
 <div className="md:hidden sticky top-0 z-10 bg-background flex items-center justify-between px-4 pt-4 pb-2 border-b border-border/30">
 <div className="flex items-center gap-2">
  <button
  type="button"
  onClick={toggleSidebar}
  className="flex items-center justify-center size-9 -ml-1.5 rounded-full text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer"
  aria-label="Open navigation"
>
  <Menu size={20} />
  </button>
  <h1 className="text-xl font-bold tracking-tight text-foreground">Analytics</h1>
 </div>

  <button
   type="button"
   title="Add"
   className="flex items-center justify-center size-9 rounded-full bg-[#007AFF] text-white hover:bg-[#0055CC] active:scale-95 transition-all cursor-pointer shadow-xs shrink-0"
  >
   <Plus size={18} strokeWidth={2.25} />
  </button>
  </div>

  {/* Content Container */}
  <div className="flex flex-col gap-8 px-4 md:px-8 lg:px-12 xl:px-16 pt-4 md:pt-14 pb-8 max-w-[1600px] w-full mx-auto">
  {/* Desktop Header */}
  <div className="hidden md:flex items-center justify-between mb-2">
   <h2 className="text-xl font-bold tracking-tight text-foreground">Analytics</h2>
   <button
   type="button"
   title="Add"
   className="flex items-center justify-center size-9 rounded-full bg-[#007AFF] text-white hover:bg-[#0055CC] active:scale-95 transition-all cursor-pointer shadow-xs shrink-0"
  >
   <Plus size={18} strokeWidth={2.25} />
   </button>
 </div>

 <Card className="border border-border rounded-xl">
  <CardHeader className="pb-3">
  <CardTitle className="text-sm font-semibold">Reports</CardTitle>
  <CardDescription className="text-xs">Analytics dashboard coming soon</CardDescription>
  </CardHeader>
  <CardContent className="flex flex-col items-center justify-center h-48 gap-3">
  <div className="flex items-center justify-center size-14 rounded-xl bg-muted">
  <BarChart3 className="size-6 text-muted-foreground" strokeWidth={1.75} />
  </div>
  <p className="text-sm text-muted-foreground">Analytics charts will appear here</p>
  </CardContent>
 </Card>
 </div>
 </>
 )
}
