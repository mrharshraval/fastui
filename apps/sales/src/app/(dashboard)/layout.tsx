"use client"

import * as React from "react"
import { usePathname, useRouter } from "next/navigation"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { MobileBottomNav } from "@/components/mobile-bottom-nav"
import { api } from "@/lib/api"

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

 {/* Main content area with bottom clearance for mobile nav */}
 <div className="flex flex-1 flex-col pb-20 md:pb-0">
  {children}
 </div>
 </SidebarInset>
 <MobileBottomNav />
 </SidebarProvider>
 )
}
