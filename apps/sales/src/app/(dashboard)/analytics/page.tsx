"use client"

import * as React from "react"
import { BarChart3 } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

export default function AnalyticsPage() {
  return (
    <>
      {/* Mobile Sticky Header */}
      <div className="md:hidden sticky top-0 z-10 bg-background flex items-center justify-between px-4 pt-4 pb-2 border-b border-border/30">
        <h1 className="text-xl font-bold tracking-tight text-foreground">Analytics</h1>
      </div>

  {/* Content Container */}
  <div className="flex flex-col gap-8 px-4 md:px-8 lg:px-12 xl:px-16 pt-4 md:pt-14 pb-8 max-w-[1600px] w-full mx-auto">
  {/* Desktop Header */}
  <div className="hidden md:flex items-center justify-between mb-2">
   <h2 className="text-xl font-bold tracking-tight text-foreground">Analytics</h2>
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
