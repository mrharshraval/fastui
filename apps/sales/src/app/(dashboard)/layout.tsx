"use client"

import * as React from "react"
import { usePathname, useRouter } from "next/navigation"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { Separator } from "@/components/ui/separator"
import {
 Breadcrumb,
 BreadcrumbItem,
 BreadcrumbList,
 BreadcrumbPage,
} from "@/components/ui/breadcrumb"
import { api } from "@/lib/api"
import { ChevronLeft, Loader2, Search, Plus } from "lucide-react"

// Breadcrumbs removed as requested

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
 const pathname = usePathname()
 const router = useRouter()

 React.useEffect(() => {
 // Graceful background session verification
 api.get<{ email?: string }>("/auth/me")
 .then((user) => {
 if (user && user.email) {
  try {
  localStorage.setItem("fastui_user", JSON.stringify(user))
  } catch {}
 }
 })
 .catch((err: any) => {
 // Only redirect to login if explicitly unauthorized (401)
 if (err?.status === 401) {
  try {
  localStorage.removeItem("fastui_user")
  } catch {}
  router.replace("/login")
 }
 })
 }, [router])

 return (
 <SidebarProvider>
 <AppSidebar />
 <SidebarInset className="bg-background flex flex-col flex-1 min-w-0">

 {/* Main content area */}
 <div className="flex flex-1 flex-col">
  {children}
 </div>
 </SidebarInset>
 </SidebarProvider>
 )
}
