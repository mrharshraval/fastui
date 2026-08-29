"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
 Users,
 Building2,
 TrendingUp,
 Percent,
 Search,
 CheckCircle2,
 Clock,
 ChevronRight,
 Filter,
 ListFilter,
 Flame,
 Globe,
 Circle,
 Plus,
 Calendar,
 AlertCircle,
 Phone,
 Mail,
 MessageSquare,
 ChevronLeft,
 ChevronDown,
 X,
 MoreHorizontal,
 Menu,
 Check,
} from "lucide-react";
import { useSidebar } from "@/components/ui/sidebar";
import {
 Card,
 CardContent,
 CardHeader,
 CardTitle,
 CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
 DropdownMenu,
 DropdownMenuItem,
 DropdownMenuCheckboxItem,
 DropdownMenuContent,
 DropdownMenuLabel,
 DropdownMenuSeparator,
 DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";

interface Stats {
 total_leads?: number;
 pipeline_value?: number;
 active_companies?: number;
 conversion_rate?: number;
}

interface FollowUpAction {
 id: string;
 contactName: string;
 company: string;
 lastInteraction: string;
 nextAction: string;
 dueDate: string;
 bucket: "overdue" | "due_today" | "upcoming" | "waiting" | "inactive";
 done: boolean;
 dealValue?: string;
}

const INITIAL_FOLLOW_UPS: FollowUpAction[] = [
 {
 id: "act-1",
 contactName: "Sarah Jenkins",
 company: "Acme Corp",
 lastInteraction: "Pricing proposal sent • 3d ago",
 nextAction: "Review contract redlines & finalize procurement",
 dueDate: "Overdue (Yesterday)",
 bucket: "overdue",
 done: false,
 dealValue: "$52,000",
 },
 {
 id: "act-2",
 contactName: "Liam Vance",
 company: "TechFlow",
 lastInteraction: "Demo call completed • Yesterday",
 nextAction: "Send SOC2 security report & enterprise tier SLA",
 dueDate: "Due Today • 3:00 PM",
 bucket: "due_today",
 done: false,
 dealValue: "$28,000",
 },
 {
 id: "act-3",
 contactName: "Elena Rostova",
 company: "Linear",
 lastInteraction: "Intro email opened • 4h ago",
 nextAction: "Schedule 20-min discovery demo with VP of Sales",
 dueDate: "Due Today • 5:30 PM",
 bucket: "due_today",
 done: false,
 dealValue: "$42,000",
 },
 {
 id: "act-4",
 contactName: "Priya Sharma",
 company: "Supabase",
 lastInteraction: "Call scheduled • Tomorrow",
 nextAction: "Executive pricing negotiation meeting",
 dueDate: "In 2 days",
 bucket: "upcoming",
 done: false,
 dealValue: "$85,000",
 },
 {
 id: "act-5",
 contactName: "Alex Rivera",
 company: "Stripe",
 lastInteraction: "Sent technical specs • 2d ago",
 nextAction: "Follow up on engineering feedback",
 dueDate: "In 3 days",
 bucket: "waiting",
 done: false,
 dealValue: "$110,000",
 },
 {
 id: "act-6",
 contactName: "Marcus Webb",
 company: "Vercel",
 lastInteraction: "Initial outreach • 8d ago",
 nextAction: "Re-engage with tailored case study & product update",
 dueDate: "No activity 8d",
 bucket: "inactive",
 done: false,
 dealValue: "$18,500",
 },
];

interface ActivityItem {
 id: string;
 action: string;
 type: "calls" | "emails";
 lead: string;
 company: string;
 time: string;
}

const INITIAL_ACTIVITIES: ActivityItem[] = [
 { id: "act-item-1", action: "Intro email opened", type: "emails", lead: "Elena Rostova", company: "Linear", time: "2 hours ago" },
 { id: "act-item-2", action: "Demo call completed", type: "calls", lead: "Liam Vance", company: "TechFlow", time: "Yesterday" },
 { id: "act-item-3", action: "Pricing proposal sent", type: "emails", lead: "Sarah Jenkins", company: "Acme Corp", time: "3 days ago" },
 { id: "act-item-4", action: "Call scheduled", type: "calls", lead: "Priya Sharma", company: "Supabase", time: "4 days ago" },
 { id: "act-item-5", action: "Follow-up email sent", type: "emails", lead: "Alex Rivera", company: "Stripe", time: "5 days ago" },
];

function Sparkline({
 data,
 isPositive,
}: {
 data: number[];
 isPositive: boolean;
}) {
 const min = Math.min(...data);
 const max = Math.max(...data);
 const range = max - min || 1;
 const width = 64;
 const height = 24;

 const points = data
 .map((val, idx) => {
 const x = (idx / (data.length - 1)) * width;
 const y = height - ((val - min) / range) * (height - 4) - 2;
 return `${x},${y}`;
 })
 .join(" ");

 const color = isPositive ? "#34C759" : "#FF3B30";

 return (
 <svg width={width} height={height} className="overflow-visible">
 <polyline
 fill="none"
 stroke={color}
 strokeWidth="2"
 strokeLinecap="round"
 strokeLinejoin="round"
 points={points}
 />
 </svg>
 );
}

export default function DashboardPage() {
 const router = useRouter();
 const { toggleSidebar } = useSidebar();
 const [stats, setStats] = React.useState<Stats>({
 total_leads: 1248,
 pipeline_value: 319500,
 active_companies: 184,
 conversion_rate: 34.2,
 });

 // Mobile View State
 const [mobileTab, setMobileTab] = React.useState<"reminder" | "activity">("reminder");
 const [mobileSearch, setMobileSearch] = React.useState("");

 // Desktop Individual Searches
 const [reminderSearch, setReminderSearch] = React.useState("");
 const [activitySearch, setActivitySearch] = React.useState("");

 // Sub-filter tabs
 const [remindersTab, setRemindersTab] = React.useState<"all" | "pending" | "upcoming">("all");
 const [activityTab, setActivityTab] = React.useState<"all" | "calls" | "emails">("all");

 // Selection states
 const [selectedReminders, setSelectedReminders] = React.useState<Set<string>>(new Set());
 const [selectedActivities, setSelectedActivities] = React.useState<Set<string>>(new Set());

 // Data State
 const [followUps, setFollowUps] = React.useState<FollowUpAction[]>(INITIAL_FOLLOW_UPS);
 const [activities, setActivities] = React.useState<ActivityItem[]>(INITIAL_ACTIVITIES);

 // Touchpoint Modal State
 const [selectedAction, setSelectedAction] = React.useState<FollowUpAction | null>(null);
 const [logOutcome, setLogOutcome] = React.useState("");
 const [nextFollowUpDate, setNextFollowUpDate] = React.useState("Tomorrow");
 const [touchpointType, setTouchpointType] = React.useState<"call" | "email" | "meeting" | "note">("call");

  React.useEffect(() => {
    api
      .get<any>("/stats")
      .then((res) => {
        if (res && typeof res === "object") {
          setStats((prev) => ({
            ...prev,
            total_leads: res.new_leads ?? prev.total_leads,
            pipeline_value: (res.proposals_sent ? res.proposals_sent * 45000 : 0) || prev.pipeline_value,
            active_companies: (res.follow_ups ? res.follow_ups * 12 : 0) || prev.active_companies,
            conversion_rate: prev.conversion_rate,
          }));

          if (Array.isArray(res.recent_activities) && res.recent_activities.length > 0) {
            const mappedActs: ActivityItem[] = res.recent_activities.map((a: any, idx: number) => ({
              id: `act-live-${idx}`,
              action: a.outcome || a.notes || "Activity logged",
              type: (a.type?.includes("call") ? "calls" : "emails"),
              lead: a.target || "Business Activity",
              company: "Client",
              time: a.time || "Recently",
            }));
            setActivities(mappedActs);
          }
        }
      })
      .catch(() => {});
  }, []);

 const handleSaveTouchpoint = (e: React.FormEvent) => {
 e.preventDefault();
 if (!selectedAction) return;

 setFollowUps((prev) =>
 prev.map((f) => {
 if (f.id === selectedAction.id) {
 return {
 ...f,
 lastInteraction: `${touchpointType.toUpperCase()}: ${logOutcome || "Touchpoint logged"} • Just now`,
 nextAction: `Follow-up on ${touchpointType} outcome`,
 dueDate: nextFollowUpDate || "In 2 days",
 bucket: nextFollowUpDate.toLowerCase().includes("today")
 ? "due_today"
 : "upcoming",
 done: false,
 };
 }
 return f;
 })
 );
 setSelectedAction(null);
 setLogOutcome("");
 };

 // Filtered Reminders (Desktop Search)
 const filteredDesktopReminders = followUps.filter((f) => {
 const matchesSearch =
 !reminderSearch ||
 f.contactName.toLowerCase().includes(reminderSearch.toLowerCase()) ||
 f.company.toLowerCase().includes(reminderSearch.toLowerCase()) ||
 f.nextAction.toLowerCase().includes(reminderSearch.toLowerCase());
 const matchesTab =
 remindersTab === "all"
 ? true
 : remindersTab === "pending"
 ? f.bucket === "overdue" || f.bucket === "due_today"
 : f.bucket === "upcoming" || f.bucket === "waiting";
 return matchesSearch && matchesTab;
 });

 // Filtered Activities (Desktop Search)
 const filteredDesktopActivities = activities.filter((a) => {
 const matchesSearch =
 !activitySearch ||
 a.action.toLowerCase().includes(activitySearch.toLowerCase()) ||
 a.lead.toLowerCase().includes(activitySearch.toLowerCase()) ||
 a.company.toLowerCase().includes(activitySearch.toLowerCase());
 const matchesTab = activityTab === "all" || a.type === activityTab;
 return matchesSearch && matchesTab;
 });

 // Mobile Filtered Lists
 const mobileFilteredReminders = followUps.filter((f) => {
 const matchesSearch =
 !mobileSearch ||
 f.contactName.toLowerCase().includes(mobileSearch.toLowerCase()) ||
 f.company.toLowerCase().includes(mobileSearch.toLowerCase()) ||
 f.nextAction.toLowerCase().includes(mobileSearch.toLowerCase());
 const matchesTab =
 remindersTab === "all"
 ? true
 : remindersTab === "pending"
 ? f.bucket === "overdue" || f.bucket === "due_today"
 : f.bucket === "upcoming" || f.bucket === "waiting";
 return matchesSearch && matchesTab;
 });

 const mobileFilteredActivities = activities.filter((a) => {
 const matchesSearch =
 !mobileSearch ||
 a.action.toLowerCase().includes(mobileSearch.toLowerCase()) ||
 a.lead.toLowerCase().includes(mobileSearch.toLowerCase()) ||
 a.company.toLowerCase().includes(mobileSearch.toLowerCase());
 const matchesTab = activityTab === "all" || a.type === activityTab;
 return matchesSearch && matchesTab;
 });

 // Capped at max 5 results per user request
 const visibleDesktopReminders = filteredDesktopReminders.slice(0, 5);
 const visibleDesktopActivities = filteredDesktopActivities.slice(0, 5);
 const visibleMobileReminders = mobileFilteredReminders.slice(0, 5);
 const visibleMobileActivities = mobileFilteredActivities.slice(0, 5);

 // Selection handlers for Reminder section
 const isReminderSelectionMode = selectedReminders.size> 0;
 const isAllRemindersSelected = visibleDesktopReminders.length> 0 && visibleDesktopReminders.every(item => selectedReminders.has(item.id));
 const isSomeRemindersSelected = visibleDesktopReminders.some(item => selectedReminders.has(item.id)) && !isAllRemindersSelected;

 const toggleAllReminders = () => {
 if (isAllRemindersSelected) {
 const newSelected = new Set(selectedReminders);
 visibleDesktopReminders.forEach(item => newSelected.delete(item.id));
 setSelectedReminders(newSelected);
 } else {
 const newSelected = new Set(selectedReminders);
 visibleDesktopReminders.forEach(item => newSelected.add(item.id));
 setSelectedReminders(newSelected);
 }
 };

 const toggleReminderItem = (id: string) => {
 const newSelected = new Set(selectedReminders);
 if (newSelected.has(id)) newSelected.delete(id);
 else newSelected.add(id);
 setSelectedReminders(newSelected);
 };

 // Selection handlers for Activity section
 const isActivitySelectionMode = selectedActivities.size> 0;
 const isAllActivitiesSelected = visibleDesktopActivities.length> 0 && visibleDesktopActivities.every(item => selectedActivities.has(item.id));
 const isSomeActivitiesSelected = visibleDesktopActivities.some(item => selectedActivities.has(item.id)) && !isAllActivitiesSelected;

 const toggleAllActivities = () => {
 if (isAllActivitiesSelected) {
 const newSelected = new Set(selectedActivities);
 visibleDesktopActivities.forEach(item => newSelected.delete(item.id));
 setSelectedActivities(newSelected);
 } else {
 const newSelected = new Set(selectedActivities);
 visibleDesktopActivities.forEach(item => newSelected.add(item.id));
 setSelectedActivities(newSelected);
 }
 };

 const toggleActivityItem = (id: string) => {
 const newSelected = new Set(selectedActivities);
 if (newSelected.has(id)) newSelected.delete(id);
 else newSelected.add(id);
 setSelectedActivities(newSelected);
 };

 const metrics = [
 {
 title: "Total Leads",
 value: (stats.total_leads ?? 1248).toLocaleString("en-US"),
 icon: Users,
 trend: "+18.4%",
 isPositive: true,
 sub: "vs last 30d",
 data: [120, 140, 135, 180, 220, 210, 260],
 },
 {
 title: "Pipeline",
 value: `$${(stats.pipeline_value ?? 319500).toLocaleString("en-US")}`,
 icon: TrendingUp,
 trend: "+24.2%",
 isPositive: true,
 sub: "Active high-intent",
 data: [200, 210, 230, 225, 260, 290, 319],
 },
 {
 title: "Companies",
 value: (stats.active_companies ?? 184).toLocaleString("en-US"),
 icon: Building2,
 trend: "+12 new",
 isPositive: true,
 sub: "42 enterprise",
 data: [150, 155, 160, 162, 170, 175, 184],
 },
 {
 title: "Win Rate",
 value: `${stats.conversion_rate ?? 34.2}%`,
 icon: Percent,
 trend: "+4.6%",
 isPositive: true,
 sub: "18d avg cycle",
 data: [28, 29, 31, 30, 32, 33, 34.2],
 },
 ];

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
 <h1 className="text-xl font-bold tracking-tight text-foreground">Home</h1>
 </div>

 <button
 type="button"
 onClick={() => router.push("/leads")}
 title="Add Lead"
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
 placeholder={mobileTab === "reminder" ? "Search reminder…" : "Search activity…"}
 value={mobileSearch}
 onChange={(e) => setMobileSearch(e.target.value)}
 className="h-10 w-full pl-10 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
 />
 </div>
 </div>

 {/* 3. Sticky Tab Bar (Scrolls up to top, locks stickily overlapping header, z-30) */}
 <div className="sticky top-0 z-30 bg-background/95 backdrop-blur-md px-4 py-2 border-b border-border/30 flex items-center justify-between gap-2 shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
 <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 min-w-0 flex-1">
 {[
 { id: "reminder", label: "Reminder" },
 { id: "activity", label: "Activity" },
 ].map((tab) => (
 <button
 key={tab.id}
 type="button"
 onClick={() => { setMobileTab(tab.id as any); setMobileSearch(""); }}
 className={`h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer shrink-0 whitespace-nowrap ${
 mobileTab === tab.id
 ? "bg-neutral-900 text-white dark:bg-white dark:text-black font-semibold shadow-sm"
 : "text-muted-foreground hover:text-foreground font-medium"
 }`}
>
 {tab.label}
 </button>
 ))}
 </div>
 </div>

 {/* 4. Mobile Content */}
 {mobileTab === "reminder" && (
 <div className="flex flex-col w-full">
 {/* Sub-filter tabs for reminder */}
 <div className="flex items-center gap-2 px-4 py-2 bg-accent/20 border-b border-border/20 overflow-x-auto no-scrollbar">
 {(["all", "pending", "upcoming"] as const).map((sub) => (
 <button
 key={sub}
 onClick={() => setRemindersTab(sub)}
 className={`text-xs capitalize font-medium px-2.5 py-1 rounded-full cursor-pointer transition-colors ${
 remindersTab === sub
 ? "bg-background text-foreground font-semibold shadow-xs"
 : "text-muted-foreground hover:text-foreground"
 }`}
>
 {sub}
 </button>
 ))}
 </div>

 <div className="flex flex-col w-full divide-y divide-border/30">
 {visibleMobileReminders.length === 0 ? (
 <div className="py-20 text-center text-sm text-muted-foreground">
 No reminders found.
 </div>
 ) : (
 visibleMobileReminders.map((item) => (
 <div
 key={item.id}
 onClick={() => setSelectedAction(item)}
 className="flex items-start justify-between py-3.5 px-4 active:bg-accent/40 transition-colors cursor-pointer"
>
 <div className="flex flex-col min-w-0 pr-3 flex-1">
 {/* Line 1: Name */}
 <div className="font-semibold text-[15px] text-foreground truncate leading-tight">
 {item.contactName}
 </div>
 {/* Line 2: Company & Next Action */}
 <div className="text-xs text-muted-foreground truncate mt-1">
 {item.company} • {item.nextAction}
 </div>
 {/* Line 3: Due Date / Urgency */}
 <div className="text-xs text-muted-foreground truncate mt-0.5">
 {item.dueDate} {item.dealValue ? `• ${item.dealValue}` : ""}
 </div>
 </div>

 {/* Far Right ⋯ Action */}
 <div onClick={(e) => e.stopPropagation()} className="shrink-0 flex items-center justify-center">
 <DropdownMenu>
 <DropdownMenuTrigger asChild>
 <button
 type="button"
 aria-label="Reminder options"
 className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer shrink-0"
>
 <MoreHorizontal size={18} />
 </button>
 </DropdownMenuTrigger>
 <DropdownMenuContent align="end" className="w-44 p-2 rounded-2xl border border-border/40 shadow-xl bg-background">
 <DropdownMenuItem
 onClick={() => setSelectedAction(item)}
 className="min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500]"
>
 Log Outcome
 </DropdownMenuItem>
 </DropdownMenuContent>
 </DropdownMenu>
 </div>
 </div>
 ))
 )}
 </div>
 </div>
 )}

 {mobileTab === "activity" && (
 <div className="flex flex-col w-full">
 {/* Sub-filter tabs for activity */}
 <div className="flex items-center gap-2 px-4 py-2 bg-accent/20 border-b border-border/20 overflow-x-auto no-scrollbar">
 {(["all", "calls", "emails"] as const).map((sub) => (
 <button
 key={sub}
 onClick={() => setActivityTab(sub)}
 className={`text-xs capitalize font-medium px-2.5 py-1 rounded-full cursor-pointer transition-colors ${
 activityTab === sub
 ? "bg-background text-foreground font-semibold shadow-xs"
 : "text-muted-foreground hover:text-foreground"
 }`}
>
 {sub}
 </button>
 ))}
 </div>

 <div className="flex flex-col w-full divide-y divide-border/30">
 {visibleMobileActivities.length === 0 ? (
 <div className="py-20 text-center text-sm text-muted-foreground">
 No activity found.
 </div>
 ) : (
 visibleMobileActivities.map((a) => (
 <div
 key={a.id}
 className="flex items-start justify-between py-3.5 px-4 active:bg-accent/40 transition-colors"
>
 <div className="flex flex-col min-w-0 pr-3 flex-1">
 {/* Line 1: Action */}
 <div className="font-semibold text-[15px] text-foreground truncate leading-tight">
 {a.action}
 </div>
 {/* Line 2: Contact & Company */}
 <div className="text-xs text-muted-foreground truncate mt-1">
 {a.lead} • {a.company}
 </div>
 {/* Line 3: Time */}
 <div className="text-xs text-muted-foreground truncate mt-0.5">
 {a.time}
 </div>
 </div>

 {/* Far Right ⋯ Action */}
 <div className="shrink-0 flex items-center justify-center">
 <DropdownMenu>
 <DropdownMenuTrigger asChild>
 <button
 type="button"
 aria-label="Activity options"
 className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer shrink-0"
>
 <MoreHorizontal size={18} />
 </button>
 </DropdownMenuTrigger>
 <DropdownMenuContent align="end" className="w-44 p-2 rounded-2xl border border-border/40 shadow-xl bg-background">
 <DropdownMenuItem className="min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500]">
 View Details
 </DropdownMenuItem>
 </DropdownMenuContent>
 </DropdownMenu>
 </div>
 </div>
 ))
 )}
 </div>
 </div>
 )}
 </div>

 {/* ─────────────────────────────────────────────────────────────
 DESKTOP VIEW (Separate Leads-Standard Sections with Guide Lines)
 Visible on screen>= md
 ───────────────────────────────────────────────────────────── */}
 <div className="hidden md:flex flex-col gap-8 px-8 lg:px-12 xl:px-16 pt-14 pb-16 max-w-[1600px] w-full mx-auto">
 {/* Top Header */}
 <div className="flex items-center justify-between mb-2">
 <h2 className="text-xl font-bold tracking-tight text-foreground">Home</h2>
 <button
 type="button"
 onClick={() => router.push("/leads")}
 title="Add Lead"
 className="flex items-center justify-center size-9 rounded-full bg-[#007AFF] text-white hover:bg-[#0055CC] active:scale-95 transition-all cursor-pointer shadow-xs shrink-0"
>
 <Plus size={18} strokeWidth={2.25} />
 </button>
 </div>

 {/* 1. Core KPI Cards Grid */}
 <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-8 -mt-4">
 {metrics.map((m) => (
 <div
 key={m.title}
 className="flex items-center justify-between gap-4 p-5 bg-neutral-100 dark:bg-neutral-800 text-card-foreground rounded-2xl"
>
 <div className="flex flex-col gap-1 min-w-0">
 <span className="text-sm font-medium text-muted-foreground whitespace-nowrap">
 {m.title}
 </span>
 <div className="text-[32px] leading-[42px] font-[652] tracking-[-0.011em] text-foreground mt-1 whitespace-nowrap">
 {m.value}
 </div>
 <div className="flex items-center gap-2 mt-1.5 whitespace-nowrap">
 <span className={`inline-flex items-center text-xs font-[600] ${m.isPositive ? "text-emerald-600 dark:text-emerald-400" : "text-destructive"}`}>
 {m.trend}
 </span>
 <span className="text-xs font-medium text-muted-foreground">{m.sub}</span>
 </div>
 </div>

 <div className="shrink-0 flex items-center justify-center opacity-80 mr-2">
 <Sparkline data={m.data} isPositive={m.isPositive} />
 </div>
 </div>
 ))}
 </div>
{/* ─────────────────────────────────────────────────────────────
 SECTION 1: REMINDER (Exact Leads-standard toolbar & table)
 ───────────────────────────────────────────────────────────── */}
 {/* Section Header Row */}
 <div className="flex items-center justify-between mb-2 mt-2">
 <h2 className="text-xl font-bold tracking-tight text-foreground">Reminder</h2>
 <div className="flex items-center gap-3">
 <div className="relative group/search">
 <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors" />
 <input
 type="text"
 placeholder="Search reminders..."
 value={reminderSearch}
 onChange={(e) => setReminderSearch(e.target.value)}
 className="h-9 w-44 sm:w-56 pl-9 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
 />
 </div>

 <button
 type="button"
 onClick={() => {
 const first = followUps[0];
 if (first) setSelectedAction(first);
 }}
 title="Add Reminder"
 className="flex items-center justify-center size-9 rounded-full bg-[#007AFF] text-white hover:bg-[#0055CC] active:scale-95 transition-all cursor-pointer shadow-xs shrink-0"
>
 <Plus size={18} strokeWidth={2.25} />
 </button>
 </div>
 </div>

 {/* Section Toolbar */}
 <div className="flex items-center justify-between min-h-9">
 {!isReminderSelectionMode ? (
 <>
 <div className="flex items-center gap-1.5">
 {(["all", "pending", "upcoming"] as const).map((tab) => (
 <button
 key={tab}
 type="button"
 onClick={() => setRemindersTab(tab)}
 className={`h-9 px-3.5 rounded-full text-sm capitalize transition-colors cursor-pointer ${
 remindersTab === tab
 ? "bg-neutral-100 dark:bg-neutral-800 text-foreground font-semibold"
 : "text-muted-foreground hover:text-foreground font-medium"
 }`}
>
 {tab}
 </button>
 ))}
 </div>

 <div className="flex items-center">
 <button
 type="button"
 aria-label="Filter"
 className="relative flex items-center justify-center size-9 rounded-full text-muted-foreground hover:text-foreground hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors cursor-pointer shrink-0"
>
 <ListFilter size={20} />
 </button>
 </div>
 </>
 ) : (
 <div className="flex items-center justify-between w-full animate-in fade-in duration-150">
 <div className="flex items-center gap-2">
 <button 
 type="button"
 onClick={() => {
 if (selectedReminders.size> 0) {
 const firstId = Array.from(selectedReminders)[0];
 const found = followUps.find(f => f.id === firstId);
 if (found) setSelectedAction(found);
 }
 }}
 className="h-9 px-4 rounded-full bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-sm font-medium text-foreground transition-colors cursor-pointer"
>
 Log Outcome
 </button>
 <button 
 type="button"
 onClick={() => {
 setFollowUps(followUps.filter(f => !selectedReminders.has(f.id)));
 setSelectedReminders(new Set());
 }}
 className="h-9 px-4 rounded-full border border-rose-400 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 text-sm font-medium transition-colors cursor-pointer"
>
 Delete
 </button>
 </div>
 <div className="flex items-center gap-3">
 <span className="text-sm text-neutral-500 font-normal">
 {selectedReminders.size} selected
 </span>
 <button
 type="button"
 onClick={() => setSelectedReminders(new Set())}
 className="flex items-center justify-center size-7 rounded-full hover:bg-neutral-100 dark:hover:bg-neutral-800 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
 title="Clear selection"
>
 <X size={20} />
 </button>
 </div>
 </div>
 )}
 </div>

 {/* Reminder Table */}
 <div className="flex flex-col -ml-12 w-[calc(100%+3rem)]">
 {/* Header Row */}
 <div className="flex items-center group/header w-full pb-2.5 select-none">
 <div className="w-9 shrink-0 flex items-center justify-center">
 <div 
 className={`transition-opacity duration-150 ${
 isReminderSelectionMode ? "opacity-100" : "opacity-0 group-hover/header:opacity-100 hover:opacity-100"
 }`}
>
 <Checkbox 
 checked={isAllRemindersSelected ? true : isSomeRemindersSelected ? 'indeterminate' : false}
 onCheckedChange={toggleAllReminders}
 aria-label="Select all visible reminders"
 />
 </div>
 </div>

 <div className="flex-1 grid grid-cols-12 gap-4 px-3 text-[14px] font-medium text-muted-foreground items-center">
 <div className="col-span-4">Contact</div>
 <div className="col-span-4">Next Action</div>
 <div className="col-span-2">Due Date</div>
 <div className="col-span-2 text-right">Status</div>
 </div>
 </div>

 {/* Rows (Max 5 results) */}
 <div className="flex flex-col w-full">
 {visibleDesktopReminders.length === 0 ? (
 <div className="py-12 text-center text-sm text-muted-foreground">
 No reminders found.
 </div>
 ) : (
 visibleDesktopReminders.map((action, idx) => {
 const isSelected = selectedReminders.has(action.id);
 const prevSelected = idx> 0 && selectedReminders.has(visibleDesktopReminders[idx - 1].id);
 const nextSelected = idx < visibleDesktopReminders.length - 1 && selectedReminders.has(visibleDesktopReminders[idx + 1].id);

 let selectionRounding = "rounded-xl";
 if (isSelected) {
 if (!prevSelected && nextSelected) {
 selectionRounding = "rounded-t-xl border-b border-neutral-200/50 dark:border-neutral-700/40";
 } else if (prevSelected && nextSelected) {
 selectionRounding = "rounded-none border-b border-neutral-200/50 dark:border-neutral-700/40";
 } else if (prevSelected && !nextSelected) {
 selectionRounding = "rounded-b-xl";
 } else {
 selectionRounding = "rounded-xl";
 }
 }

 return (
 <div key={action.id} className="flex items-center group/row w-full my-[1px] relative">
 <div className="w-9 shrink-0 flex items-center justify-center">
 <div 
 className={`transition-opacity duration-150 ${
 isSelected ? "opacity-100" : "opacity-0 group-hover/row:opacity-100 hover:opacity-100"
 }`}
 onClick={(e) => e.stopPropagation()}
>
 <Checkbox 
 checked={isSelected}
 onCheckedChange={() => toggleReminderItem(action.id)}
 aria-label={`Select ${action.contactName}`}
 />
 </div>
 </div>

 <div 
 onClick={() => setSelectedAction(action)}
 className={`flex-1 grid grid-cols-12 gap-4 px-3 py-3 text-sm items-center transition-colors cursor-pointer ${
 isSelected 
 ? `bg-neutral-100/90 dark:bg-neutral-800/80 ${selectionRounding}` 
 : "hover:bg-neutral-100/50 dark:hover:bg-neutral-800/40 rounded-xl"
 }`}
>
 <div className="col-span-4 font-medium text-foreground truncate">
 {action.contactName}
 <span className="text-xs text-muted-foreground ml-2 font-normal">
 {action.company}
 </span>
 </div>
 <div className="col-span-4 text-muted-foreground text-xs truncate">
 {action.nextAction}
 </div>
 <div className="col-span-2 text-muted-foreground text-xs truncate">
 {action.dueDate}
 </div>
 <div className="col-span-2 flex justify-end">
 {action.bucket === "overdue" ? (
 <Badge variant="destructive" className="text-xs rounded-full px-2.5 py-0.5 font-normal">
 Overdue
 </Badge>
 ) : action.bucket === "due_today" ? (
 <Badge variant="secondary" className="text-xs rounded-full px-2.5 py-0.5 font-normal bg-amber-500/15 text-amber-600 dark:text-amber-400">
 Due Today
 </Badge>
 ) : (
 <Badge variant="secondary" className="text-xs rounded-full px-2.5 py-0.5 font-normal">
 Upcoming
 </Badge>
 )}
 </div>
 </div>
 </div>
 );
 })
 )}
 </div>
 </div>

 {/* ─────────────────────────────────────────────────────────────
 SECTION 2: ACTIVITY (Exact Leads-standard toolbar & table)
 ───────────────────────────────────────────────────────────── */}
 {/* Section Header Row */}
 <div className="flex items-center justify-between mb-2 mt-4">
 <h2 className="text-xl font-bold tracking-tight text-foreground">Activity</h2>
 <div className="flex items-center gap-3">
 <div className="relative group/search">
 <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors" />
 <input
 type="text"
 placeholder="Search activities..."
 value={activitySearch}
 onChange={(e) => setActivitySearch(e.target.value)}
 className="h-9 w-44 sm:w-56 pl-9 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
 />
 </div>

 <button
 type="button"
 title="Add Activity"
 className="flex items-center justify-center size-9 rounded-full bg-[#007AFF] text-white hover:bg-[#0055CC] active:scale-[0.97] transition-all cursor-pointer shadow-sm shrink-0"
>
 <Plus size={20} />
 </button>
 </div>
 </div>

 {/* Section Toolbar */}
 <div className="flex items-center justify-between min-h-9">
 {!isActivitySelectionMode ? (
 <>
 <div className="flex items-center gap-1.5">
 {(["all", "calls", "emails"] as const).map((tab) => (
 <button
 key={tab}
 type="button"
 onClick={() => setActivityTab(tab)}
 className={`h-9 px-3.5 rounded-full text-sm capitalize transition-colors cursor-pointer ${
 activityTab === tab
 ? "bg-neutral-100 dark:bg-neutral-800 text-foreground font-semibold"
 : "text-muted-foreground hover:text-foreground font-medium"
 }`}
>
 {tab}
 </button>
 ))}
 </div>

 <div className="flex items-center">
 <button
 type="button"
 aria-label="Filter"
 className="relative flex items-center justify-center size-9 rounded-full text-muted-foreground hover:text-foreground hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors cursor-pointer shrink-0"
>
 <ListFilter size={20} />
 </button>
 </div>
 </>
 ) : (
 <div className="flex items-center justify-between w-full animate-in fade-in duration-150">
 <div className="flex items-center gap-2">
 <button 
 type="button"
 onClick={() => {
 setActivities(activities.filter(a => !selectedActivities.has(a.id)));
 setSelectedActivities(new Set());
 }}
 className="h-9 px-4 rounded-full border border-rose-400 text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 text-sm font-medium transition-colors cursor-pointer"
>
 Delete
 </button>
 </div>
 <div className="flex items-center gap-3">
 <span className="text-sm text-neutral-500 font-normal">
 {selectedActivities.size} selected
 </span>
 <button
 type="button"
 onClick={() => setSelectedActivities(new Set())}
 className="flex items-center justify-center size-7 rounded-full hover:bg-neutral-100 dark:hover:bg-neutral-800 text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
 title="Clear selection"
>
 <X size={20} />
 </button>
 </div>
 </div>
 )}
 </div>

 {/* Activity Table */}
 <div className="flex flex-col -ml-12 w-[calc(100%+3rem)]">
 {/* Header Row */}
 <div className="flex items-center group/header w-full pb-2.5 select-none">
 <div className="w-9 shrink-0 flex items-center justify-center">
 <div 
 className={`transition-opacity duration-150 ${
 isActivitySelectionMode ? "opacity-100" : "opacity-0 group-hover/header:opacity-100 hover:opacity-100"
 }`}
>
 <Checkbox 
 checked={isAllActivitiesSelected ? true : isSomeActivitiesSelected ? 'indeterminate' : false}
 onCheckedChange={toggleAllActivities}
 aria-label="Select all visible activities"
 />
 </div>
 </div>

 <div className="flex-1 grid grid-cols-12 gap-4 px-3 text-[14px] font-medium text-muted-foreground items-center">
 <div className="col-span-4">Action</div>
 <div className="col-span-4">Contact & Company</div>
 <div className="col-span-2">Type</div>
 <div className="col-span-2 text-right">Time</div>
 </div>
 </div>

 {/* Rows (Max 5 results) */}
 <div className="flex flex-col w-full">
 {visibleDesktopActivities.length === 0 ? (
 <div className="py-12 text-center text-sm text-muted-foreground">
 No activity found.
 </div>
 ) : (
 visibleDesktopActivities.map((a, idx) => {
 const isSelected = selectedActivities.has(a.id);
 const prevSelected = idx> 0 && selectedActivities.has(visibleDesktopActivities[idx - 1].id);
 const nextSelected = idx < visibleDesktopActivities.length - 1 && selectedActivities.has(visibleDesktopActivities[idx + 1].id);

 let selectionRounding = "rounded-xl";
 if (isSelected) {
 if (!prevSelected && nextSelected) {
 selectionRounding = "rounded-t-xl border-b border-neutral-200/50 dark:border-neutral-700/40";
 } else if (prevSelected && nextSelected) {
 selectionRounding = "rounded-none border-b border-neutral-200/50 dark:border-neutral-700/40";
 } else if (prevSelected && !nextSelected) {
 selectionRounding = "rounded-b-xl";
 } else {
 selectionRounding = "rounded-xl";
 }
 }

 return (
 <div key={a.id} className="flex items-center group/row w-full my-[1px] relative">
 <div className="w-9 shrink-0 flex items-center justify-center">
 <div 
 className={`transition-opacity duration-150 ${
 isSelected ? "opacity-100" : "opacity-0 group-hover/row:opacity-100 hover:opacity-100"
 }`}
 onClick={(e) => e.stopPropagation()}
>
 <Checkbox 
 checked={isSelected}
 onCheckedChange={() => toggleActivityItem(a.id)}
 aria-label={`Select ${a.action}`}
 />
 </div>
 </div>

 <div 
 className={`flex-1 grid grid-cols-12 gap-4 px-3 py-3 text-sm items-center transition-colors cursor-pointer ${
 isSelected 
 ? `bg-neutral-100/90 dark:bg-neutral-800/80 ${selectionRounding}` 
 : "hover:bg-neutral-100/50 dark:hover:bg-neutral-800/40 rounded-xl"
 }`}
>
 <div className="col-span-4 font-medium text-foreground truncate">
 {a.action}
 </div>
 <div className="col-span-4 text-muted-foreground text-xs truncate">
 {a.lead} • {a.company}
 </div>
 <div className="col-span-2 text-muted-foreground text-xs capitalize truncate">
 {a.type}
 </div>
 <div className="col-span-2 text-muted-foreground text-xs text-right truncate">
 {a.time}
 </div>
 </div>
 </div>
 );
 })
 )}
 </div>
 </div>
 </div>

 {/* Touchpoint Logging Modal */}
 {selectedAction && (
 <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in">
 <div className="bg-card border border-border/60 rounded-2xl max-w-md w-full p-6 shadow-2xl flex flex-col gap-4">
 <div className="flex items-center justify-between">
 <div>
 <h3 className="text-lg font-semibold text-foreground">
 Log Touchpoint Outcome
 </h3>
 <p className="text-xs text-muted-foreground mt-0.5">
 {selectedAction.contactName} <span className="ml-1.5">{selectedAction.company}</span>
 </p>
 </div>
 <button
 type="button"
 onClick={() => setSelectedAction(null)}
 className="text-muted-foreground hover:text-foreground cursor-pointer"
>
 <X size={20} />
 </button>
 </div>

 <form onSubmit={handleSaveTouchpoint} className="flex flex-col gap-4">
 {/* Interaction Type */}
 <div className="flex flex-col gap-1.5">
 <label className="text-sm font-semibold text-foreground">
 Touchpoint Type
 </label>
 <div className="grid grid-cols-4 gap-2">
 {[
 { id: "call", label: "Call", icon: Phone },
 { id: "email", label: "Email", icon: Mail },
 { id: "meeting", label: "Meeting", icon: Calendar },
 { id: "note", label: "Note", icon: MessageSquare },
 ].map((t) => (
 <button
 key={t.id}
 type="button"
 onClick={() => setTouchpointType(t.id as any)}
 className={`flex flex-col items-center gap-1 p-2 rounded-xl text-sm font-medium transition-all cursor-pointer ${
 touchpointType === t.id
 ? "bg-[#007AFF] text-white font-semibold shadow-none"
 : "bg-accent text-muted-foreground hover:text-foreground hover:bg-accent/70"
 }`}
>
 <t.icon className="size-4" />
 <span>{t.label}</span>
 </button>
 ))}
 </div>
 </div>

 {/* Outcome / Notes */}
 <div className="flex flex-col gap-1.5">
 <label className="text-sm font-semibold text-foreground">
 Interaction Outcome
 </label>
 <textarea
 rows={3}
 placeholder="e.g. Connected on call, reviewed enterprise tier requirements, agreed to send revised SLA..."
 value={logOutcome}
 onChange={(e) => setLogOutcome(e.target.value)}
 className="w-full rounded-xl bg-accent/40 p-3 text-base text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-[#007AFF]/30 resize-none border-none"
 required
 />
 </div>

 {/* Next Follow-up Date */}
 <div className="flex flex-col gap-1.5">
 <label className="text-sm font-semibold text-foreground">
 Next Follow-up Date
 </label>
 <div className="grid grid-cols-3 gap-2">
 {["Tomorrow", "In 2 days", "Next Week"].map((date) => (
 <button
 key={date}
 type="button"
 onClick={() => setNextFollowUpDate(date)}
 className={`p-2 rounded-xl text-sm font-medium transition-all cursor-pointer ${
 nextFollowUpDate === date
 ? "bg-[#007AFF] text-white font-semibold shadow-none"
 : "bg-accent text-muted-foreground hover:text-foreground hover:bg-accent/70"
 }`}
>
 {date}
 </button>
 ))}
 </div>
 </div>

 {/* Action Buttons */}
 <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/40">
 <button
 type="button"
 onClick={() => setSelectedAction(null)}
 className="h-9 px-3 text-sm font-medium text-muted-foreground hover:text-foreground cursor-pointer transition-colors rounded-2xl hover:bg-accent"
>
 Cancel
 </button>
 <button
 type="submit"
 className="h-9 px-4 text-sm font-semibold rounded-2xl cursor-pointer bg-[#007AFF] text-white hover:bg-[#0055CC] transition-colors active:scale-[0.98]"
>
 Save & Update
 </button>
 </div>
 </form>
 </div>
 </div>
 )}
 </>
 );
}
