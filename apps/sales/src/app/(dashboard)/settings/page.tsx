"use client"

import * as React from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Plus, Menu } from "lucide-react"
import { useSidebar } from "@/components/ui/sidebar"

export default function SettingsPage() {
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
   <h1 className="text-xl font-bold tracking-tight text-foreground">Settings</h1>
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
   <h2 className="text-xl font-bold tracking-tight text-foreground">Settings</h2>
   <button
   type="button"
   title="Add"
   className="flex items-center justify-center size-9 rounded-full bg-[#007AFF] text-white hover:bg-[#0055CC] active:scale-95 transition-all cursor-pointer shadow-xs shrink-0"
  >
   <Plus size={18} strokeWidth={2.25} />
   </button>
  </div>

  <Card className="bg-card rounded-xl">
   <CardHeader className="pb-4">
   <CardTitle className="text-sm font-semibold">Profile</CardTitle>
   <CardDescription className="text-xs">Update your name and email</CardDescription>
   </CardHeader>
   <CardContent className="flex flex-col gap-4">
   <div className="space-y-1.5">
    <Label className="text-sm font-medium">Display Name</Label>
    <Input placeholder="Your name" className="h-10 bg-accent/30 rounded-full text-sm border-none" />
   </div>
   <div className="space-y-1.5">
    <Label className="text-sm font-medium">Email</Label>
    <Input type="email" placeholder="name@domain.com" className="h-10 bg-accent/30 rounded-full text-sm border-none" />
   </div>
   <Button className="w-fit h-9 rounded-2xl text-sm border-none">Save Changes</Button>
   </CardContent>
  </Card>

  <Card className="bg-card rounded-xl">
   <CardHeader className="pb-4">
   <CardTitle className="text-sm font-semibold">Password</CardTitle>
   <CardDescription className="text-xs">Update your password</CardDescription>
   </CardHeader>
   <CardContent className="flex flex-col gap-4">
   <div className="space-y-1.5">
    <Label className="text-sm font-medium">Current Password</Label>
    <Input type="password" placeholder="Current password" className="h-10 bg-accent/30 rounded-full text-sm border-none" />
   </div>
   <div className="space-y-1.5">
    <Label className="text-sm font-medium">New Password</Label>
    <Input type="password" placeholder="New password" className="h-10 bg-accent/30 rounded-full text-sm border-none" />
   </div>
   <Button variant="secondary" className="w-fit h-9 rounded-2xl text-sm border-none">Update Password</Button>
   </CardContent>
  </Card>

  <Card className="bg-rose-500/10 rounded-xl">
   <CardHeader className="pb-4">
   <CardTitle className="text-sm font-semibold text-rose-400">Danger Zone</CardTitle>
   <CardDescription className="text-xs">Irreversible actions</CardDescription>
   </CardHeader>
   <CardContent>
   <Button variant="secondary" className="h-9 rounded-2xl text-sm text-rose-400 bg-rose-500/20 hover:bg-rose-500/30 border-none">Delete Account</Button>
   </CardContent>
  </Card>
  </div>
 </>
 )
}
