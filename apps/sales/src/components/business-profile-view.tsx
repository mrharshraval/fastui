"use client"

import * as React from "react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { Plus, ChevronDown, MoreHorizontal, ArrowLeft, X, Check } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { getNotificationPermissionState, subscribeToPushNotifications } from "@/lib/push-notifications"


import { cn } from "@/lib/utils"
import { api } from "@/lib/api"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export interface BusinessDetail {
  id: string
  business_name: string
  category?: string
  address?: string
  city?: string
  state?: string
  country?: string
  location?: string
  website?: string
  phone?: string
  email?: string
  whatsapp?: string
  created_at: string
  is_lead?: boolean
  qualification_status?: string
  stage?: string
}

interface ActivityItem {
  id: string
  user_name: string
  action: string
  notes?: string
  timestamp: string
}

interface ReminderItem {
  id: string
  title: string
  due_date: string
  notes?: string
  status?: "pending" | "completed"
  user_name?: string
  timestamp?: string
}

function formatActivityAction(type?: string, fallback?: string): string {
  if (!type) return fallback || "Activity logged"
  const t = type.toLowerCase()
  if (t === "website_visited" || t === "website") return "Visited website"
  if (t === "call_initiated" || t === "call") return "Call initiated"
  if (t === "whatsapp_opened" || t === "whatsapp") return "WhatsApp opened"
  if (t === "email_initiated" || t === "email") return "Email initiated"
  if (t === "note_added" || t === "note") return "Note added"
  if (t === "reminder_created" || t === "reminder") return "Reminder set"
  if (t === "status_changed") return "Stage changed"
  if (t === "proposal_sent") return "Proposal sent"
  if (t === "business_discovered" || t === "discover") return "Discovered lead"
  if (t === "added_to_leads") return "Added to Leads"
  return fallback || type
}

function formatActivityTimestamp(dateInput?: string | Date): string {
  if (!dateInput) {
    const d = new Date()
    return `${d.getDate()} ${d.toLocaleDateString("en-US", { month: "short" })}`
  }
  const date = typeof dateInput === "string" ? new Date(dateInput) : dateInput
  if (isNaN(date.getTime())) {
    const d = new Date()
    return `${d.getDate()} ${d.toLocaleDateString("en-US", { month: "short" })}`
  }
  const day = date.getDate()
  const month = date.toLocaleDateString("en-US", { month: "short" })
  return `${day} ${month}`
}

function ActivityItemRow({
  act,
  onDelete,
}: {
  act: ActivityItem
  onDelete: () => void
}) {
  const [isExpanded, setIsExpanded] = React.useState(false)
  const notes = act.notes?.trim()
  const MAX_CHARS = 8
  const isLong = Boolean(notes && notes.length > MAX_CHARS)

  return (
    <div className="flex flex-col py-1.5 first:pt-0 last:pb-0">
      {/* 1. Top Row: Title on Left, Date + Overflow Menu on Right */}
      <div className="flex items-start justify-between gap-3 w-full">
        <span className="text-[13.5px] font-[500] text-foreground leading-snug min-w-0 flex-1 break-words">
          {act.action}
        </span>

        <div className="flex items-center gap-2 shrink-0 ml-auto pt-0.5">
          <span className="text-xs text-muted-foreground tabular-nums font-normal select-none">
            {act.timestamp}
          </span>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                className="flex items-center justify-center size-6 rounded-md text-muted-foreground/70 hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer shrink-0 -mr-1"
                aria-label="Activity options"
              >
                <MoreHorizontal size={14} />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-32">
              <DropdownMenuItem
                onClick={onDelete}
                className="min-h-8 px-2.5 rounded-xl cursor-pointer text-xs font-medium text-destructive focus:text-destructive"
              >
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* 2. Additional detail line only when note/context exists */}
      {notes && (
        <div className="text-xs text-muted-foreground/90 mt-0.5 leading-relaxed break-words">
          {isLong && !isExpanded ? (
            <span>
              {notes.slice(0, MAX_CHARS).trim()}{" "}
              <span className="text-muted-foreground/50 select-none">·</span>{" "}
              <button
                type="button"
                onClick={() => setIsExpanded(true)}
                className="inline text-foreground font-medium hover:underline text-xs cursor-pointer"
              >
                Read more
              </button>
            </span>
          ) : isLong && isExpanded ? (
            <span>
              {notes}{" "}
              <span className="text-muted-foreground/50 select-none">·</span>{" "}
              <button
                type="button"
                onClick={() => setIsExpanded(false)}
                className="inline text-muted-foreground hover:text-foreground font-medium hover:underline text-xs cursor-pointer"
              >
                Show less
              </button>
            </span>
          ) : (
            <span>{notes}</span>
          )}
        </div>
      )}

      {/* 3. Actor / User on its own line at the bottom */}
      <div className="text-xs text-muted-foreground font-normal mt-0.5">
        {act.user_name || "Harsh"}
      </div>
    </div>
  )
}

export function BusinessProfileView() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()

  // ─── Current authenticated user (for activity attribution) ───
  const [currentUser, setCurrentUser] = React.useState<{ user_id?: number; email?: string; name?: string } | null>(null)

  React.useEffect(() => {
    // 1. Instant hydration from cached identity
    try {
      const stored = localStorage.getItem("fastui_user")
      if (stored) {
        const parsed = JSON.parse(stored)
        if (parsed?.email) setCurrentUser(parsed)
      }
    } catch {}
    // 2. Authoritative sync from backend session
    api.get<{ user_id?: number; email?: string; name?: string }>("/auth/me")
      .then((data) => { if (data?.email) setCurrentUser(data) })
      .catch(() => {})
  }, [])

  // Derive a short display name for the current user
  const currentUserName = React.useMemo(() => {
    if (!currentUser) return "You"
    if (currentUser.name) return currentUser.name
    if (currentUser.email) {
      const prefix = currentUser.email.split("@")[0]
      return prefix.charAt(0).toUpperCase() + prefix.slice(1)
    }
    return "You"
  }, [currentUser])

  const [business, setBusiness] = React.useState<BusinessDetail | null>(null)

  const [activities, setActivities] = React.useState<ActivityItem[]>([])
  const [reminders, setReminders] = React.useState<ReminderItem[]>([])
  const [activeTab, setActiveTab] = React.useState<"activity" | "reminders" | "details">("activity")
  const [loading, setLoading] = React.useState(true)
  const [addingToLeads, setAddingToLeads] = React.useState(false)
  const [showBusinessDetails, setShowBusinessDetails] = React.useState(false)
  const [showContactDetails, setShowContactDetails] = React.useState(false)
  
  // Shared bottom sheet state
  const [activeSheet, setActiveSheet] = React.useState<"note" | "reminder" | null>(null)
  const [keyboardHeight, setKeyboardHeight] = React.useState(0)

  // Note sheet state
  const [noteInput, setNoteInput] = React.useState("")
  const [submittingNote, setSubmittingNote] = React.useState(false)

  // Reminder sheet state
  const [reminderText, setReminderText] = React.useState("")
  const [reminderDate, setReminderDate] = React.useState(() => {
    const d = new Date()
    d.setDate(d.getDate() + 1)
    return d.toISOString().split("T")[0]
  })
  const [reminderTime, setReminderTime] = React.useState("10:00")
  const [reminderContact, setReminderContact] = React.useState("")
  const [reminderPickerMode, setReminderPickerMode] = React.useState<"date" | "time" | null>(null)
  const [submittingReminder, setSubmittingReminder] = React.useState(false)
  const pickerTimerRef = React.useRef<NodeJS.Timeout | null>(null)
  const pickerRef = React.useRef<HTMLDivElement | null>(null)
  const reminderTextareaRef = React.useRef<HTMLTextAreaElement | null>(null)
  const noteTextareaRef = React.useRef<HTMLTextAreaElement | null>(null)

  // Auto-resize reminder textarea up to 4 lines (96px max) then fix height & scroll
  React.useEffect(() => {
    if (activeSheet === "reminder" && reminderTextareaRef.current) {
      const el = reminderTextareaRef.current
      el.style.height = "auto"
      el.style.height = `${Math.min(el.scrollHeight, 96)}px`
    }
  }, [reminderText, activeSheet])

  // Auto-resize note textarea up to 4 lines (96px max) then fix height & scroll
  React.useEffect(() => {
    if (activeSheet === "note" && noteTextareaRef.current) {
      const el = noteTextareaRef.current
      el.style.height = "auto"
      el.style.height = `${Math.min(el.scrollHeight, 96)}px`
    }
  }, [noteInput, activeSheet])

  // Reset inactivity timer on any interaction (4s)
  const resetPickerTimer = React.useCallback(() => {
    if (pickerTimerRef.current) {
      clearTimeout(pickerTimerRef.current)
      pickerTimerRef.current = null
    }

    if (reminderPickerMode) {
      pickerTimerRef.current = setTimeout(() => {
        setReminderPickerMode(null)
      }, 4000)
    }
  }, [reminderPickerMode])

  React.useEffect(() => {
    resetPickerTimer()
    return () => {
      if (pickerTimerRef.current) {
        clearTimeout(pickerTimerRef.current)
      }
    }
  }, [reminderPickerMode, resetPickerTimer])

  // Next 14 days generator for inline scheduling
  const NEXT_DAYS = React.useMemo(() => {
    const days: { dateStr: string; label: string }[] = []
    const now = new Date()
    for (let i = 0; i < 14; i++) {
      const d = new Date(now)
      d.setDate(now.getDate() + i)
      const year = d.getFullYear()
      const month = String(d.getMonth() + 1).padStart(2, "0")
      const day = String(d.getDate()).padStart(2, "0")
      const dateStr = `${year}-${month}-${day}`
      const label = i === 0 ? "Today" : i === 1 ? "Tomorrow" : d.toLocaleDateString("en-US", { month: "short", day: "numeric" })
      days.push({ dateStr, label })
    }
    return days
  }, [])

  // All day time slots in 30-minute intervals (7:00 AM to 10:00 PM)
  const TIME_SLOTS = React.useMemo(() => {
    const slots: { label: string; val: string }[] = []
    for (let hour = 7; hour <= 22; hour++) {
      for (const min of [0, 30]) {
        if (hour === 22 && min > 0) break
        const val = `${String(hour).padStart(2, "0")}:${String(min).padStart(2, "0")}`
        const dummyDate = new Date()
        dummyDate.setHours(hour, min, 0, 0)
        const label = dummyDate.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
        slots.push({ label, val })
      }
    }
    return slots
  }, [])

  // Keyboard viewport listener
  React.useEffect(() => {
    if (!activeSheet) {
      setKeyboardHeight(0)
      return
    }

    const originalOverflow = document.body.style.overflow
    document.body.style.overflow = "hidden"

    const updateKeyboard = () => {
      if (typeof window === "undefined" || !window.visualViewport) return
      const vv = window.visualViewport
      const offset = Math.max(0, window.innerHeight - vv.height - vv.offsetTop)
      setKeyboardHeight(offset)
    }

    if (window.visualViewport) {
      window.visualViewport.addEventListener("resize", updateKeyboard)
      window.visualViewport.addEventListener("scroll", updateKeyboard)
      updateKeyboard()
    }

    return () => {
      document.body.style.overflow = originalOverflow
      if (window.visualViewport) {
        window.visualViewport.removeEventListener("resize", updateKeyboard)
        window.visualViewport.removeEventListener("scroll", updateKeyboard)
      }
    }
  }, [activeSheet])

  // Fetch business & activities
  React.useEffect(() => {
    if (!id || id === "undefined") {
      setLoading(false)
      return
    }

    const numericId = parseInt(id.replace(/[^0-9]/g, ""), 10)

    const fetchBackend = async () => {
      try {
        if (!isNaN(numericId) && numericId > 0) {
          const comp = await api.get<any>(`/businesses/${numericId}`)
          if (comp && comp.business_name) {
            setBusiness({
              id: String(comp.id),
              business_name: comp.business_name,
              category: comp.category || undefined,
              address: comp.address || undefined,
              city: comp.city || undefined,
              state: comp.state || undefined,
              country: comp.country || undefined,
              location: (comp.city && comp.state && comp.country && !comp.city.includes(comp.state))
                ? [comp.city, comp.state, comp.country].filter(Boolean).join(", ")
                : (comp.city || comp.address || comp.country || undefined),
              website: comp.website || undefined,
              phone: comp.phone || undefined,
              email: comp.email || undefined,
              whatsapp: comp.phone
                ? (() => {
                    const digits = comp.phone.replace(/[^0-9]/g, "")
                    const clean = digits.startsWith("0") && digits.length === 11 ? digits.slice(1) : digits
                    return clean.length === 10 ? `91${clean}` : clean
                  })()
                : undefined,
              created_at: comp.created_at || new Date().toISOString(),
              is_lead: comp.is_lead,
              qualification_status: comp.qualification_status,
              stage: comp.pipeline_stage || comp.stage
            })

            // Fetch activities
            try {
              const acts = await api.get<any[]>(`/businesses/${numericId}/activities`)
              if (Array.isArray(acts)) {
                setActivities(
                  acts.map((a: any) => ({
                    id: String(a.id),
                    // Use server-returned user_name if present, else current user name
                    user_name: a.user_name || currentUserName,
                    action: formatActivityAction(a.type, a.outcome),
                    notes: a.notes || undefined,
                    timestamp: formatActivityTimestamp(a.created_at ? new Date(a.created_at) : new Date())
                  }))
                )
              } else {
                setActivities([])
              }
            } catch {
              setActivities([])
            }

            // Fetch reminders
            try {
              const rems = await api.get<any[]>(`/businesses/${numericId}/reminders`)
              if (Array.isArray(rems)) {
                setReminders(
                  rems.map((r: any) => ({
                    id: String(r.id),
                    title: r.title,
                    due_date: r.due_at ? formatActivityTimestamp(new Date(r.due_at)) : "No date",
                    notes: r.notes || undefined,
                    status: r.status || "pending",
                    // Use server-returned user_name if present, else current user name
                    user_name: r.user_name || currentUserName,
                    timestamp: formatActivityTimestamp(r.created_at ? new Date(r.created_at) : new Date())
                  }))
                )
              } else {
                setReminders([])
              }
            } catch {
              setReminders([])
            }
            return
          }
        }
      } catch {
        // Business not found
      }

      setBusiness(null)
      setActivities([])
      setReminders([])
    }

    fetchBackend().finally(() => setLoading(false))
  }, [id])

  // Normal browser/router history back navigation
  const handleBack = () => {
    router.back()
  }

  // Handle promoting prospect to lead
  const handleAddToLeads = async () => {
    if (!business || addingToLeads) return
    setAddingToLeads(true)

    const numericId = parseInt(business.id.replace(/[^0-9]/g, ""), 10)
    try {
      if (!isNaN(numericId) && numericId > 0) {
        await api.post(`/prospects/${numericId}/add-to-leads`, {})
      }
      setBusiness((prev) => prev ? { ...prev, is_lead: true } : null)
      
      const newActivity: ActivityItem = {
        id: `act-promote-${Date.now()}`,
        user_name: currentUserName,
        action: "Approved",
        notes: "Promoted to sales pipeline",
        timestamp: formatActivityTimestamp(new Date())
      }
      setActivities((prev) => [newActivity, ...prev])
    } catch {
      // Ignore API errors
    } finally {
      setAddingToLeads(false)
    }
  }

  // Handle contact actions
  const handleAction = async (
    actionType: "website" | "call" | "email" | "whatsapp",
    targetValue: string
  ) => {
    if (!business) return

    let actionLabel = ""
    let actionDesc = ""

    if (actionType === "website") {
      const url = targetValue.startsWith("http") ? targetValue : `https://${targetValue}`
      window.open(url, "_blank", "noopener,noreferrer")
      actionLabel = "Visited website"
      actionDesc = "Website visit logged"
    } else if (actionType === "call") {
      window.location.href = `tel:${targetValue}`
      actionLabel = "Call initiated"
      actionDesc = "Call logged"
    } else if (actionType === "email") {
      window.location.href = `mailto:${targetValue}`
      actionLabel = "Email initiated"
      actionDesc = "Email action logged"
    } else if (actionType === "whatsapp") {
      const cleanNum = targetValue.replace(/[^0-9]/g, "")
      window.open(`https://wa.me/${cleanNum}`, "_blank", "noopener,noreferrer")
      actionLabel = "WhatsApp opened"
      actionDesc = "WhatsApp action logged"
    }

    const newActivity: ActivityItem = {
      id: `act-local-${Date.now()}`,
      user_name: currentUserName,
      action: actionLabel,
      notes: targetValue,
      timestamp: formatActivityTimestamp(new Date())
    }

    setActivities((prev) => [newActivity, ...prev])

    // Persist to API
    try {
      const numericId = parseInt(business.id.replace(/[^0-9]/g, ""), 10)
      if (!isNaN(numericId) && numericId > 0) {
        if (actionType === "website") {
          await api.post(`/businesses/${numericId}/activities`, {
            type: "website_visited",
            channel: "website",
            outcome: actionLabel,
            notes: targetValue
          })
        } else {
          await api.post(`/businesses/${numericId}/outreach`, {
            channel: actionType,
            recipient: targetValue,
            status: "initiated",
            notes: actionLabel
          })
        }
      }
    } catch {
      // Ignore API errors
    }
  }

  // Handle adding notes via Bottom Sheet
  const handleSaveNote = async () => {
    if (!noteInput.trim() || !business || submittingNote) return
    setSubmittingNote(true)

    const noteText = noteInput.trim()
    const newActivity: ActivityItem = {
      id: `act-note-${Date.now()}`,
      user_name: currentUserName,
      action: "Note added",
      notes: noteText,
      timestamp: formatActivityTimestamp(new Date())
    }

    setActivities((prev) => [newActivity, ...prev])
    setNoteInput("")
    setActiveSheet(null)
    setSubmittingNote(false)

    // Persist to API
    try {
      const numericId = parseInt(business.id.replace(/[^0-9]/g, ""), 10)
      if (!isNaN(numericId) && numericId > 0) {
        await api.post(`/businesses/${numericId}/notes`, {
          content: noteText
        })
      }
    } catch {
      // Ignore API errors
    }
  }

  // Handle saving reminder via Bottom Sheet
  const handleSaveReminder = async () => {
    if (!reminderText.trim() || !business || submittingReminder) return
    setSubmittingReminder(true)

    const text = reminderText.trim()
    let formattedDue = reminderDate
    let isoDue = new Date().toISOString()
    try {
      const [year, month, day] = reminderDate.split("-").map(Number)
      const d = new Date(year, month - 1, day)
      const monthDay = d.toLocaleDateString("en-US", { month: "short", day: "numeric" })
      
      const [hour, minute] = reminderTime.split(":").map(Number)
      d.setHours(hour, minute, 0, 0)
      isoDue = d.toISOString()
      const timeDisplay = d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
      formattedDue = `${monthDay} · ${timeDisplay}`
    } catch {
      formattedDue = `${reminderDate} ${reminderTime}`
    }

    const newReminder: ReminderItem = {
      id: `rem-${Date.now()}`,
      title: text,
      due_date: formattedDue,
      notes: reminderContact ? `Contact: ${reminderContact}` : undefined,
      status: "pending",
      user_name: currentUserName,
      timestamp: formatActivityTimestamp(new Date())
    }

    setReminders((prev) => [newReminder, ...prev])

    const newActivity: ActivityItem = {
      id: `act-reminder-${Date.now()}`,
      user_name: currentUserName,
      action: "Reminder set",
      notes: `${text} (${formattedDue})${reminderContact ? ` · Contact: ${reminderContact}` : ""}`,
      timestamp: formatActivityTimestamp(new Date())
    }

    setActivities((prev) => [newActivity, ...prev])
    setReminderText("")
    setActiveSheet(null)
    setSubmittingReminder(false)

    // Persist to API
    try {
      const numericId = parseInt(business.id.replace(/[^0-9]/g, ""), 10)
      if (!isNaN(numericId) && numericId > 0) {
        await api.post(`/businesses/${numericId}/reminders`, {
          title: text,
          due_at: isoDue,
          notes: reminderContact ? `Contact: ${reminderContact}` : undefined
        })
      }
    } catch {
      // Ignore API errors
    }

    // Seamlessly request push notification permission if default
    try {
      if (getNotificationPermissionState() === "default") {
        subscribeToPushNotifications().catch(() => {})
      }
    } catch {
      // Ignore
    }

  }

  if (loading) {
    return (
      <div className="flex flex-col h-full w-full min-h-screen bg-background animate-pulse">
        {/* Mobile Header Skeleton */}
        <div className="md:hidden sticky top-0 z-10 bg-background flex items-center justify-between px-4 pt-4 pb-2 border-b border-border/30">
          <Skeleton className="size-9 rounded-full" />
          <Skeleton className="h-8 w-16 rounded-full" />
        </div>

        {/* Desktop Main Container */}
        <div className="flex flex-col flex-1 px-4 md:px-8 lg:px-12 xl:px-16 pt-4 md:pt-14 pb-16 max-w-[1600px] mx-auto w-full">
          {/* Desktop Header: Back Button Skeleton */}
          <div className="hidden md:flex items-center justify-end mb-8">
            <Skeleton className="h-9 w-20 rounded-full" />
          </div>

          {/* Business Identity Skeleton (Centered) */}
          <div className="flex flex-col items-center w-full max-w-[540px] mx-auto text-center pt-2 md:pt-4 pb-6">
            <Skeleton className="size-16 rounded-full" />
            <Skeleton className="h-7 w-48 rounded-lg mt-3" />
            <Skeleton className="h-4 w-32 rounded-md mt-2" />

            {/* Contact Action Pills Skeleton */}
            <div className="flex items-center justify-center gap-2 mt-6 md:mt-7 flex-wrap">
              <Skeleton className="h-8 w-20 rounded-full" />
              <Skeleton className="h-8 w-18 rounded-full" />
              <Skeleton className="h-8 w-18 rounded-full" />
              <Skeleton className="h-8 w-22 rounded-full" />
            </div>
          </div>

          {/* Tabs Bar Skeleton */}
          <div className="w-full max-w-[540px] mx-auto mt-7 mb-6 pb-2.5 border-b border-border/30 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Skeleton className="h-9 w-20 rounded-full" />
              <Skeleton className="h-9 w-24 rounded-full" />
              <Skeleton className="h-9 w-18 rounded-full" />
            </div>
            <Skeleton className="size-8 rounded-full" />
          </div>

          {/* Timeline List Skeleton */}
          <div className="w-full max-w-[540px] mx-auto flex flex-col gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex flex-col pb-3.5 border-b border-border/20 gap-2">
                <div className="flex items-center justify-between">
                  <Skeleton className="h-4 w-36 rounded" />
                  <Skeleton className="h-3.5 w-14 rounded" />
                </div>
                <Skeleton className="h-3.5 w-3/4 rounded-sm" />
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!business) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-3">
        <p className="text-sm text-muted-foreground">Business not found</p>
        <button
          type="button"
          onClick={handleBack}
          className="h-9 px-4 rounded-full bg-accent hover:bg-accent/80 text-foreground text-sm font-medium inline-flex items-center gap-1.5 transition-colors cursor-pointer"
        >
          <ArrowLeft size={16} />
          <span>Back</span>
        </button>
      </div>
    )
  }

  // Location string construction
  const cityRegionCountry = [business.city, business.state, business.country].filter(Boolean).join(", ")
  const locationString = business.location || cityRegionCountry
  const initialLetter = (business.business_name || "B").charAt(0).toUpperCase()

  const addressContent = (business.address || cityRegionCountry) ? (
    <div className="flex flex-col">
      {business.address && <span>{business.address}</span>}
      {cityRegionCountry && <span>{cityRegionCountry}</span>}
    </div>
  ) : null

  // Collect available business details
  const businessDetailsEntries = [
    { label: "Business name", value: business.business_name },
    business.category ? { label: "Category", value: business.category } : null,
    addressContent ? { label: "Address", value: addressContent } : null,
  ].filter(Boolean) as { label: string; value: React.ReactNode }[]

  // Collect available contact details (actionable values)
  const contactDetailsEntries = [
    business.website ? {
      label: "Website",
      value: (
        <button
          type="button"
          onClick={() => handleAction("website", business.website!)}
          className="text-foreground hover:underline text-left cursor-pointer transition-colors"
        >
          {business.website.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')}
        </button>
      )
    } : null,
    business.phone ? {
      label: "Phone",
      value: (
        <button
          type="button"
          onClick={() => handleAction("call", business.phone!)}
          className="text-foreground hover:underline text-left cursor-pointer transition-colors"
        >
          {business.phone}
        </button>
      )
    } : null,
    business.email ? {
      label: "Email",
      value: (
        <button
          type="button"
          onClick={() => handleAction("email", business.email!)}
          className="text-foreground hover:underline text-left cursor-pointer transition-colors"
        >
          {business.email}
        </button>
      )
    } : null,
    (business.whatsapp || business.phone) ? {
      label: "WhatsApp",
      value: (
        <button
          type="button"
          onClick={() => handleAction("whatsapp", business.whatsapp || business.phone!)}
          className="text-foreground hover:underline text-left cursor-pointer transition-colors"
        >
          {business.whatsapp || business.phone}
        </button>
      )
    } : null,
  ].filter(Boolean) as { label: string; value: React.ReactNode }[]

  return (
    <div className="flex flex-col h-full w-full min-h-screen bg-background">
      {/* ─────────────────────────────────────────────────────────────
          1. HEADER (Mobile Back Header)
         ───────────────────────────────────────────────────────────── */}
      {/* Mobile Sticky Header */}
      <div className="md:hidden sticky top-0 z-10 bg-background flex items-center justify-between px-4 pt-4 pb-2 border-b border-border/30">
        <button
          type="button"
          onClick={handleBack}
          className="flex items-center gap-1.5 h-8 px-3 rounded-full bg-accent/60 hover:bg-accent text-foreground text-xs font-medium transition-colors cursor-pointer shrink-0"
        >
          <ArrowLeft size={14} />
          <span>Back</span>
        </button>
      </div>


      {/* Desktop Main Container */}
      <div className="flex flex-col flex-1 px-4 md:px-8 lg:px-12 xl:px-16 pt-4 md:pt-14 pb-16 max-w-[1600px] mx-auto w-full">
        {/* Desktop Header: Back Button Right */}
        <div className="hidden md:flex items-center justify-end mb-8">
          <button
            type="button"
            onClick={handleBack}
            className="h-9 px-4 rounded-full bg-accent/60 hover:bg-accent text-foreground text-sm font-medium transition-colors cursor-pointer"
          >
            Back
          </button>
        </div>

        {/* ─────────────────────────────────────────────────────────────
            2. BUSINESS IDENTITY (Centered, Minimal)
           ───────────────────────────────────────────────────────────── */}
        <div className="flex flex-col items-center w-full max-w-[540px] mx-auto text-center pt-2 md:pt-4 pb-6">
          {/* Circular Business Initial/Avatar */}
          <div className="size-16 rounded-full bg-accent/70 text-foreground flex items-center justify-center text-xl font-bold tracking-tight shadow-none select-none">
            {initialLetter}
          </div>

          {/* Business Name */}
          <h2 className="text-xl md:text-2xl font-bold tracking-tight text-foreground mt-3">
            {business.business_name}
          </h2>

          {/* Location */}
          {locationString && (
            <p className="text-sm text-muted-foreground/80 mt-1">
              {locationString}
            </p>
          )}

          {/* ─────────────────────────────────────────────────────────────
              3. CONTACT ACTIONS (Pills) & CONTEXTUAL LIFECYCLE ACTION
             ───────────────────────────────────────────────────────────── */}
          <div className="flex items-center justify-center gap-2 mt-6 md:mt-7 flex-wrap">
            {business.website && (
              <button
                type="button"
                onClick={() => handleAction("website", business.website!)}
                className="h-8 px-4 rounded-full bg-accent/60 hover:bg-accent text-foreground text-sm font-medium transition-all active:scale-[0.98] cursor-pointer"
              >
                Website
              </button>
            )}

            {business.phone && (
              <button
                type="button"
                onClick={() => handleAction("call", business.phone!)}
                className="h-8 px-4 rounded-full bg-accent/60 hover:bg-accent text-foreground text-sm font-medium transition-all active:scale-[0.98] cursor-pointer"
              >
                Phone
              </button>
            )}

            {business.email && (
              <button
                type="button"
                onClick={() => handleAction("email", business.email!)}
                className="h-8 px-4 rounded-full bg-accent/60 hover:bg-accent text-foreground text-sm font-medium transition-all active:scale-[0.98] cursor-pointer"
              >
                Email
              </button>
            )}

            {(business.whatsapp || business.phone) && (
              <button
                type="button"
                onClick={() => handleAction("whatsapp", business.whatsapp || business.phone!)}
                className="h-8 px-4 rounded-full bg-accent/60 hover:bg-accent text-foreground text-sm font-medium transition-all active:scale-[0.98] cursor-pointer"
              >
                WhatsApp
              </button>
            )}

            {/* Contextual Action: Approve (for unconverted prospects) */}
            {!business.is_lead && (
              <button
                type="button"
                onClick={handleAddToLeads}
                disabled={addingToLeads}
                className="h-8 px-4 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium transition-all active:scale-[0.98] cursor-pointer inline-flex items-center justify-center disabled:opacity-50"
              >
                <span>{addingToLeads ? "Approving…" : "Approve"}</span>
              </button>
            )}
          </div>
        </div>

        {/* ─────────────────────────────────────────────────────────────
            TABS BAR (Activity, Reminders, Details, + Contextual Action)
           ───────────────────────────────────────────────────────────── */}
        <div className="w-full max-w-[540px] mx-auto mt-7 mb-6 pb-2.5 border-b border-border/30 flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 min-w-0">
            {(
              [
                { id: "activity", label: "Activity" },
                { id: "reminders", label: "Reminders" },
                { id: "details", label: "Details" },
              ] as const
            ).map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer shrink-0 whitespace-nowrap",
                  activeTab === tab.id
                    ? "bg-primary text-primary-foreground font-semibold"
                    : "text-muted-foreground hover:text-foreground font-medium"
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Far-Right Contextual '+' Action */}
          <div className="shrink-0 flex items-center">
            {activeTab === "activity" && (
              <button
                type="button"
                onClick={() => setActiveSheet("note")}
                className="flex items-center justify-center size-8 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground active:scale-95 transition-all cursor-pointer"
                aria-label="Add note"
                title="Add note"
              >
                <Plus size={16} />
              </button>
            )}

            {activeTab === "reminders" && (
              <button
                type="button"
                onClick={() => setActiveSheet("reminder")}
                className="flex items-center justify-center size-8 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground active:scale-95 transition-all cursor-pointer"
                aria-label="Add reminder"
                title="Add reminder"
              >
                <Plus size={16} />
              </button>
            )}
          </div>
        </div>

        {/* ─────────────────────────────────────────────────────────────
            TAB CONTENT: ACTIVITY
           ───────────────────────────────────────────────────────────── */}
        {activeTab === "activity" && (
          <div className="w-full max-w-[540px] mx-auto pb-8 animate-in fade-in duration-150">
            {activities.length === 0 ? (
              <p className="text-left text-xs text-muted-foreground py-2">
                No activity recorded yet.
              </p>
            ) : (
              <div className="flex flex-col space-y-4">
                {activities.map((act) => (
                  <ActivityItemRow
                    key={act.id}
                    act={act}
                    onDelete={async () => {
                      setActivities((prev) => prev.filter((a) => a.id !== act.id))
                      const numId = parseInt(act.id.replace(/[^0-9]/g, ""), 10)
                      if (!isNaN(numId) && numId > 0 && act.id.includes("note")) {
                        try {
                          await api.delete(`/notes/${numId}`)
                        } catch {}
                      }
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────
            TAB CONTENT: REMINDERS
           ───────────────────────────────────────────────────────────── */}
        {activeTab === "reminders" && (
          <div className="w-full max-w-[540px] mx-auto pb-8 animate-in fade-in duration-150">
            {/* Reminders List */}
            <div className="flex flex-col divide-y divide-border/20">
              {reminders.length === 0 ? (
                <p className="text-left text-xs text-muted-foreground py-2">
                  No reminders scheduled.
                </p>
              ) : (
                reminders.map((rem) => (
                  <div key={rem.id} className="flex flex-col py-3 first:pt-0 last:pb-0">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-[14px] font-medium text-foreground leading-snug">
                        {rem.title}
                      </span>

                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-xs text-muted-foreground/70 font-normal">
                          {rem.timestamp || "Aug 28"}
                        </span>

                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <button
                              type="button"
                              className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer shrink-0"
                              aria-label="Reminder options"
                            >
                              <MoreHorizontal size={16} />
                            </button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-36">
                            <DropdownMenuItem
                              onClick={async () => {
                                setReminders((prev) => prev.filter((r) => r.id !== rem.id))
                                const numId = parseInt(rem.id.replace(/[^0-9]/g, ""), 10)
                                if (!isNaN(numId) && numId > 0) {
                                  try {
                                    await api.patch(`/reminders/${numId}`, { status: "completed" })
                                  } catch {}
                                }
                              }}
                              className="min-h-8 px-2.5 rounded-xl cursor-pointer text-xs font-medium"
                            >
                              Complete
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={async () => {
                                setReminders((prev) => prev.filter((r) => r.id !== rem.id))
                                const numId = parseInt(rem.id.replace(/[^0-9]/g, ""), 10)
                                if (!isNaN(numId) && numId > 0) {
                                  try {
                                    await api.delete(`/reminders/${numId}`)
                                  } catch {}
                                }
                              }}
                              className="min-h-8 px-2.5 rounded-xl cursor-pointer text-xs font-medium text-destructive focus:text-destructive"
                            >
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>


                    <span className="text-xs text-muted-foreground mt-0.5 font-normal">
                      {rem.user_name || "Harsh"}
                    </span>

                    {rem.notes && (
                      <p className="text-[13px] text-muted-foreground/90 mt-1 leading-relaxed break-words">
                        {rem.notes}
                      </p>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* ─────────────────────────────────────────────────────────────
            TAB CONTENT: DETAILS
           ───────────────────────────────────────────────────────────── */}
        {activeTab === "details" && (
          <div className="w-full max-w-[540px] mx-auto pb-8 flex flex-col animate-in fade-in duration-150">
            {/* Business details section */}
            <div className="py-2 border-b border-border/40 first:border-t-0">
              <button
                type="button"
                onClick={() => setShowBusinessDetails((prev) => !prev)}
                className="flex items-center justify-between w-full text-left py-2 text-sm font-semibold text-foreground hover:text-foreground/80 transition-colors cursor-pointer group"
              >
                <span>Business details</span>
                <ChevronDown
                  size={16}
                  className={cn(
                    "text-muted-foreground/60 transition-transform duration-200",
                    showBusinessDetails && "rotate-180"
                  )}
                />
              </button>

              {showBusinessDetails && (
                <div className="flex flex-col gap-3 text-sm pt-2 pb-3 animate-in fade-in slide-in-from-top-1 duration-200">
                  {businessDetailsEntries.map((entry, i) => (
                    <div key={i} className="flex flex-col gap-0.5">
                      <span className="text-xs text-muted-foreground font-medium">
                        {entry.label}
                      </span>
                      <div className="text-foreground font-normal break-words">
                        {entry.value}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Contact details section */}
            {contactDetailsEntries.length > 0 && (
              <div className="py-2 border-b border-border/40">
                <button
                  type="button"
                  onClick={() => setShowContactDetails((prev) => !prev)}
                  className="flex items-center justify-between w-full text-left py-2 text-sm font-semibold text-foreground hover:text-foreground/80 transition-colors cursor-pointer group"
                >
                  <span>Contact details</span>
                  <ChevronDown
                    size={16}
                    className={cn(
                      "text-muted-foreground/60 transition-transform duration-200",
                      showContactDetails && "rotate-180"
                    )}
                  />
                </button>

                {showContactDetails && (
                  <div className="flex flex-col gap-3 text-sm pt-2 pb-3 animate-in fade-in slide-in-from-top-1 duration-200">
                    {contactDetailsEntries.map((entry, i) => (
                      <div key={i} className="flex flex-col gap-0.5">
                        <span className="text-xs text-muted-foreground font-medium">
                          {entry.label}
                        </span>
                        <div className="text-foreground font-normal break-words">
                          {entry.value}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ─────────────────────────────────────────────────────────────
          SHARED APPLE-STYLE FLOATING BOTTOM SHEET (Note / Reminder)
         ───────────────────────────────────────────────────────────── */}
      {activeSheet && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center p-3.5 sm:p-4 md:pb-6 pointer-events-auto transition-[padding] duration-200 ease-out"
          style={{
            paddingBottom: keyboardHeight > 0 ? `${keyboardHeight + 12}px` : undefined,
          }}
        >
          {/* Lightly Dimmed Backdrop */}
          <div
            onClick={() => setActiveSheet(null)}
            className="fixed inset-0 bg-backdrop backdrop-blur-[1px] transition-opacity animate-in fade-in duration-200"
          />

          {/* Floating Sheet Surface */}
          <div
            onClick={(e) => {
              if (reminderPickerMode && pickerRef.current && !pickerRef.current.contains(e.target as Node)) {
                const isTrigger = (e.target as HTMLElement).closest("[data-picker-trigger]")
                if (!isTrigger) {
                  setReminderPickerMode(null)
                }
              }
            }}
            className="relative z-10 w-full max-w-md bg-card rounded-[28px] shadow-sheet border border-border/30 p-5 pt-3 pb-4 animate-in slide-in-from-bottom-6 duration-200 flex flex-col max-h-[calc(100dvh-3rem)] overflow-hidden"
          >
            {/* Subtle Drag Handle */}
            <div className="w-9 h-1 rounded-full bg-muted-foreground/25 mx-auto mb-3 shrink-0" />

            {/* Header: Left-aligned Title + Right-aligned Close Button */}
            <div className="flex items-center justify-between pb-3 border-b border-border/20 shrink-0">
              <h2 className="text-base font-semibold text-foreground tracking-tight">
                {activeSheet === "note" ? "Note" : "Reminder"}
              </h2>
              <button
                type="button"
                onClick={() => setActiveSheet(null)}
                className="size-7 rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent/60 transition-colors cursor-pointer"
                aria-label="Close"
              >
                <X size={16} />
              </button>
            </div>

            {/* Content for Add Note */}
            {activeSheet === "note" && (
              <div className="flex flex-col pt-3 min-h-0 flex-1">
                {/* Borderless Note Text Area (Auto-expands up to 4 lines, then scrolls internally) */}
                <textarea
                  ref={noteTextareaRef}
                  autoFocus
                  placeholder="Write a note…"
                  value={noteInput}
                  onChange={(e) => {
                    setNoteInput(e.target.value)
                    const target = e.target
                    target.style.height = "auto"
                    target.style.height = `${Math.min(target.scrollHeight, 96)}px`
                  }}
                  rows={1}
                  className="w-full max-h-[96px] overflow-y-auto p-0 bg-transparent border-0 focus:outline-none focus:ring-0 text-sm text-foreground placeholder:text-muted-foreground/50 resize-none leading-relaxed overscroll-contain apple-scrollbar"
                />

                <div className="flex items-center justify-end pt-3 mt-2 border-t border-border/20 shrink-0">
                  <button
                    type="button"
                    onClick={handleSaveNote}
                    disabled={!noteInput.trim() || submittingNote}
                    className="h-8 px-4 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold text-xs transition-all cursor-pointer disabled:opacity-35 active:scale-[0.98]"
                  >
                    Save
                  </button>
                </div>
              </div>
            )}

            {/* Content for Add Reminder */}
            {activeSheet === "reminder" && (
              <div className="flex flex-col pt-3 gap-3.5">
                {/* Borderless Reminder Text Area (Auto-expands up to 4 lines, then scrolls internally) */}
                <textarea
                  ref={reminderTextareaRef}
                  autoFocus
                  placeholder="Follow up with Sarah…"
                  value={reminderText}
                  onChange={(e) => {
                    setReminderText(e.target.value)
                    const target = e.target
                    target.style.height = "auto"
                    target.style.height = `${Math.min(target.scrollHeight, 96)}px`
                  }}
                  rows={1}
                  className="w-full max-h-[96px] overflow-y-auto p-0 bg-transparent border-0 focus:outline-none focus:ring-0 text-sm text-foreground placeholder:text-muted-foreground/50 resize-none leading-relaxed overscroll-contain apple-scrollbar"
                />

                {/* Inline Date Picker */}
                {reminderPickerMode === "date" && (
                  <div
                    ref={pickerRef}
                    onScroll={resetPickerTimer}
                    onTouchStart={resetPickerTimer}
                    onTouchMove={resetPickerTimer}
                    onPointerDown={resetPickerTimer}
                    onPointerMove={resetPickerTimer}
                    onWheel={resetPickerTimer}
                    className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1 -mx-1 px-1 border-t border-border/20 pt-2.5 animate-in fade-in duration-150"
                  >
                    {NEXT_DAYS.map((d) => {
                      const isSelected = reminderDate === d.dateStr
                      return (
                        <button
                          key={d.dateStr}
                          type="button"
                          onClick={() => {
                            setReminderDate(d.dateStr)
                            setReminderPickerMode(null)
                          }}
                          className={cn(
                            "h-7 px-3 rounded-full text-xs transition-colors cursor-pointer shrink-0 whitespace-nowrap select-none",
                            isSelected
                              ? "bg-primary text-primary-foreground font-semibold"
                              : "bg-secondary hover:bg-secondary/80 text-muted-foreground hover:text-foreground font-medium"
                          )}
                        >
                          {d.label}
                        </button>
                      )
                    })}
                  </div>
                )}

                {/* Inline Time Picker */}
                {reminderPickerMode === "time" && (
                  <div
                    ref={pickerRef}
                    onScroll={resetPickerTimer}
                    onTouchStart={resetPickerTimer}
                    onTouchMove={resetPickerTimer}
                    onPointerDown={resetPickerTimer}
                    onPointerMove={resetPickerTimer}
                    onWheel={resetPickerTimer}
                    className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1 -mx-1 px-1 border-t border-border/20 pt-2.5 animate-in fade-in duration-150"
                  >
                    {TIME_SLOTS.map((t) => {
                      const isSelected = reminderTime === t.val
                      return (
                        <button
                          key={t.val}
                          type="button"
                          onClick={() => {
                            setReminderTime(t.val)
                            setReminderPickerMode(null)
                          }}
                          className={cn(
                            "h-7 px-3 rounded-full text-xs transition-colors cursor-pointer shrink-0 whitespace-nowrap select-none",
                            isSelected
                              ? "bg-primary text-primary-foreground font-semibold"
                              : "bg-secondary hover:bg-secondary/80 text-muted-foreground hover:text-foreground font-medium"
                          )}
                        >
                          {t.label}
                        </button>
                      )
                    })}
                  </div>
                )}

                {/* Bottom Row: Simple Borderless Date & Time Triggers at Bottom-Left, Save at Bottom-Right */}
                <div className="flex items-center justify-between pt-2 mt-1 border-t border-border/20 shrink-0">
                  <div className="flex items-center gap-1.5 text-xs select-none">
                    <button
                      type="button"
                      data-picker-trigger
                      onClick={() => setReminderPickerMode((prev) => (prev === "date" ? null : "date"))}
                      className={cn(
                        "transition-colors cursor-pointer p-0 bg-transparent border-0 focus:outline-none",
                        reminderPickerMode === "date"
                          ? "text-foreground font-semibold"
                          : "text-muted-foreground hover:text-foreground font-normal"
                      )}
                    >
                      {(() => {
                        try {
                          const [y, m, d] = reminderDate.split("-").map(Number)
                          const dateObj = new Date(y, m - 1, d)
                          return dateObj.toLocaleDateString("en-US", { month: "short", day: "numeric" })
                        } catch {
                          return reminderDate
                        }
                      })()}
                    </button>

                    <button
                      type="button"
                      data-picker-trigger
                      onClick={() => setReminderPickerMode((prev) => (prev === "time" ? null : "time"))}
                      className={cn(
                        "transition-colors cursor-pointer p-0 bg-transparent border-0 focus:outline-none",
                        reminderPickerMode === "time"
                          ? "text-foreground font-semibold"
                          : "text-muted-foreground hover:text-foreground font-normal"
                      )}
                    >
                      {(() => {
                        try {
                          const [h, min] = reminderTime.split(":").map(Number)
                          const timeObj = new Date()
                          timeObj.setHours(h, min)
                          return timeObj.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })
                        } catch {
                          return reminderTime
                        }
                      })()}
                    </button>
                  </div>

                  <button
                    type="button"
                    onClick={handleSaveReminder}
                    disabled={!reminderText.trim() || submittingReminder}
                    className="h-8 px-4 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold text-xs transition-all cursor-pointer disabled:opacity-35 active:scale-[0.98]"
                  >
                    Save
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
