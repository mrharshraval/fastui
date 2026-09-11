"use client";

import * as React from "react";
import { Search, MoreHorizontal } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { FollowUpAction, ActivityFeedModel } from "../types";

interface DashboardMobileListProps {
  reminders: FollowUpAction[];
  activities: ActivityFeedModel[];
  onSelectAction: (action: FollowUpAction) => void;
}

export function DashboardMobileList({
  reminders,
  activities,
  onSelectAction,
}: DashboardMobileListProps) {
  const [tab, setTab] = React.useState<"reminder" | "activity">("reminder");
  const [search, setSearch] = React.useState("");
  const [remindersTab, setRemindersTab] = React.useState<"all" | "pending" | "upcoming">("all");
  const [activityTab, setActivityTab] = React.useState<"all" | "calls" | "emails">("all");

  const filteredReminders = reminders.filter((f) => {
    const matchesSearch =
      !search ||
      f.contactName.toLowerCase().includes(search.toLowerCase()) ||
      f.company.toLowerCase().includes(search.toLowerCase()) ||
      f.nextAction.toLowerCase().includes(search.toLowerCase());
    const matchesTab =
      remindersTab === "all"
        ? true
        : remindersTab === "pending"
        ? f.bucket === "overdue" || f.bucket === "due_today"
        : f.bucket === "upcoming" || f.bucket === "waiting";
    return matchesSearch && matchesTab;
  });

  const filteredActivities = activities.filter((a) => {
    const matchesSearch =
      !search ||
      a.action.toLowerCase().includes(search.toLowerCase()) ||
      a.lead.toLowerCase().includes(search.toLowerCase()) ||
      a.company.toLowerCase().includes(search.toLowerCase());
    const matchesTab = activityTab === "all" || a.type === activityTab;
    return matchesSearch && matchesTab;
  });

  const visibleReminders = filteredReminders.slice(0, 5);
  const visibleActivities = filteredActivities.slice(0, 5);

  return (
    <div className="flex flex-col w-full md:hidden pb-16">
      {/* 1. Mobile Header */}
      <div className="sticky top-0 z-10 bg-background flex items-center justify-between px-4 pt-4 pb-2">
        <h1 className="text-xl font-bold tracking-tight text-foreground">Home</h1>
      </div>

      {/* 2. Search Bar */}
      <div className="relative z-0 px-4 pt-2 pb-4 bg-background">
        <div className="relative w-full group/search">
          <Search
            size={16}
            className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors"
          />
          <input
            type="text"
            placeholder={tab === "reminder" ? "Search reminder…" : "Search activity…"}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-10 w-full pl-10 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
          />
        </div>
      </div>

      {/* 3. Sticky Tab Bar */}
      <div className="sticky top-0 z-30 bg-background/95 backdrop-blur-md px-4 py-2 border-b border-border/30 flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 min-w-0 flex-1">
          {[
            { id: "reminder", label: "Follow-ups" },
            { id: "activity", label: "Activity" },
          ].map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => {
                setTab(t.id as any);
                setSearch("");
              }}
              className={`h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer shrink-0 whitespace-nowrap ${
                tab === t.id
                  ? "bg-primary text-primary-foreground font-semibold"
                  : "text-muted-foreground hover:text-foreground font-medium"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* 4. Mobile Content */}
      {tab === "reminder" && (
        <div className="flex flex-col w-full">
          <div className="flex items-center gap-2 px-4 py-2 bg-accent/20 border-b border-border/20 overflow-x-auto no-scrollbar">
            {(["all", "pending", "upcoming"] as const).map((sub) => (
              <button
                key={sub}
                onClick={() => setRemindersTab(sub)}
                className={`text-xs capitalize font-medium px-2.5 py-1 rounded-full cursor-pointer transition-colors ${
                  remindersTab === sub
                    ? "bg-background text-foreground font-semibold"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {sub}
              </button>
            ))}
          </div>

          <div className="flex flex-col w-full divide-y divide-border/30">
            {visibleReminders.length === 0 ? (
              <div className="py-20 text-center text-sm text-muted-foreground">
                No follow-ups found.
              </div>
            ) : (
              visibleReminders.map((item) => (
                <div
                  key={item.id}
                  onClick={() => onSelectAction(item)}
                  className="flex items-start justify-between py-3.5 px-4 active:bg-accent/40 transition-colors cursor-pointer"
                >
                  <div className="flex flex-col min-w-0 pr-3 flex-1">
                    <div className="font-semibold text-[15px] text-foreground truncate leading-tight">
                      {item.contactName}
                    </div>
                    <div className="text-xs text-muted-foreground truncate mt-1">
                      {item.company} • {item.nextAction}
                    </div>
                    <div className="text-xs text-muted-foreground truncate mt-0.5">
                      {item.dueDate} {item.dealValue ? `• ${item.dealValue}` : ""}
                    </div>
                  </div>

                  <div
                    onClick={(e) => e.stopPropagation()}
                    className="shrink-0 flex items-center justify-center"
                  >
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
                      <DropdownMenuContent align="end" className="w-44">
                        <DropdownMenuItem
                          onClick={() => onSelectAction(item)}
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

      {tab === "activity" && (
        <div className="flex flex-col w-full">
          <div className="flex items-center gap-2 px-4 py-2 bg-accent/20 border-b border-border/20 overflow-x-auto no-scrollbar">
            {(["all", "calls", "emails"] as const).map((sub) => (
              <button
                key={sub}
                onClick={() => setActivityTab(sub)}
                className={`text-xs capitalize font-medium px-2.5 py-1 rounded-full cursor-pointer transition-colors ${
                  activityTab === sub
                    ? "bg-background text-foreground font-semibold"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {sub}
              </button>
            ))}
          </div>

          <div className="flex flex-col w-full divide-y divide-border/30">
            {visibleActivities.length === 0 ? (
              <div className="py-20 text-center text-sm text-muted-foreground">
                No activity found.
              </div>
            ) : (
              visibleActivities.map((a) => (
                <div
                  key={a.id}
                  className="flex items-start justify-between py-3.5 px-4 active:bg-accent/40 transition-colors"
                >
                  <div className="flex flex-col min-w-0 pr-3 flex-1">
                    <div className="font-semibold text-[15px] text-foreground truncate leading-tight">
                      {a.action}
                    </div>
                    <div className="text-xs text-muted-foreground truncate mt-1">
                      {a.lead} • {a.company}
                    </div>
                    <div className="text-xs text-muted-foreground truncate mt-0.5">
                      {a.time}
                    </div>
                  </div>

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
                      <DropdownMenuContent align="end" className="w-44">
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
  );
}
