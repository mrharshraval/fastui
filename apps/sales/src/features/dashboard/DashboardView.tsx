"use client";

import * as React from "react";
import { KpiSummary } from "./components/KpiSummary";
import { RemindersSection } from "./components/RemindersSection";
import { ActivitiesSection } from "./components/ActivitiesSection";
import { DashboardMobileList } from "./components/DashboardMobileList";
import { TouchpointModal } from "./components/TouchpointModal";
import { dashboardApi } from "./api";
import { formatReminderDisplay, getReminderUrgency } from "@/shared/lib/date";
import type { StatsModel, FollowUpAction, ActivityFeedModel } from "./types";

interface DashboardViewProps {
  initialStats?: StatsModel;
  initialFollowUps?: FollowUpAction[];
  initialActivities?: ActivityFeedModel[];
}

export function DashboardView({
  initialStats = {
    total_leads: 0,
    pipeline_value: 0,
    active_companies: 0,
    conversion_rate: 0,
  },
  initialFollowUps = [],
  initialActivities = [],
}: DashboardViewProps) {
  const [stats, setStats] = React.useState<StatsModel>(initialStats);
  const [followUps, setFollowUps] = React.useState<FollowUpAction[]>(initialFollowUps);
  const [activities, setActivities] = React.useState<ActivityFeedModel[]>(initialActivities);
  const [selectedAction, setSelectedAction] = React.useState<FollowUpAction | null>(null);

  React.useEffect(() => {
    if (!initialFollowUps.length && !initialActivities.length) {
      dashboardApi
        .getStats()
        .then((res) => {
          if (res) {
            setStats({
              total_leads: res.new_leads ?? 0,
              pipeline_value: res.proposals_sent ? res.proposals_sent * 45000 : 0,
              active_companies: res.follow_ups ? res.follow_ups * 12 : 0,
              conversion_rate: 0,
            });

            if (Array.isArray(res.recent_activities) && res.recent_activities.length > 0) {
              const mappedActs: ActivityFeedModel[] = res.recent_activities.map((a, idx) => ({
                id: `act-live-${idx}`,
                action: a.outcome || a.notes || "Activity logged",
                type: a.type?.includes("call") ? "calls" : "emails",
                lead: a.target || "Business Activity",
                company: "Client",
                time: a.time || "Recently",
              }));
              setActivities(mappedActs);
            }
          }
        })
        .catch(() => {});

      dashboardApi
        .getReminders()
        .then((res) => {
          if (Array.isArray(res)) {
            const mapped: FollowUpAction[] = res.map((f) => ({
              id: String(f.id),
              contactName: f.contact_name || f.title || "Contact",
              company: "Company",
              lastInteraction: f.notes || f.title || "Pending touchpoint",
              nextAction: f.notes || f.title || "Follow up",
              dueDate: f.due_at ? formatReminderDisplay(f.due_at) : "Upcoming",
              bucket: getReminderUrgency(f.due_at),
              done: f.status?.toLowerCase() === "completed" || f.status?.toLowerCase() === "done",
            }));
            setFollowUps(mapped);
          }
        })
        .catch(() => {});
    }
  }, [initialFollowUps.length, initialActivities.length]);

  const handleSaveTouchpoint = async (
    action: FollowUpAction,
    type: "call" | "email" | "meeting" | "note",
    outcome: string,
    nextDate: string
  ) => {
    setFollowUps((prev) =>
      prev.map((f) => {
        if (f.id === action.id) {
          return {
            ...f,
            lastInteraction: `${type.toUpperCase()}: ${outcome || "Touchpoint logged"} • Just now`,
            nextAction: `Follow-up on ${type} outcome`,
            dueDate: nextDate || "In 2 days",
            bucket: nextDate.toLowerCase().includes("today") ? "due_today" : "upcoming",
            done: false,
          };
        }
        return f;
      })
    );

    const numId = parseInt(action.id.replace(/[^0-9]/g, ""), 10);
    if (!isNaN(numId) && numId > 0) {
      try {
        await dashboardApi.updateReminder(numId, {
          notes: `${type.toUpperCase()}: ${outcome || "Logged touchpoint"}`,
          status: "completed",
        });
      } catch (err) {
        console.error("[DashboardView] Update reminder failed:", err);
      }
    }
  };

  const handleDeleteReminders = async (ids: string[]) => {
    const idSet = new Set(ids);
    setFollowUps((prev) => prev.filter((f) => !idSet.has(f.id)));
    for (const id of ids) {
      const numId = parseInt(id.replace(/[^0-9]/g, ""), 10);
      if (!isNaN(numId) && numId > 0) {
        dashboardApi.deleteReminder(numId).catch(() => {});
      }
    }
  };

  const handleDeleteActivities = (ids: string[]) => {
    const idSet = new Set(ids);
    setActivities((prev) => prev.filter((a) => !idSet.has(a.id)));
  };

  return (
    <>
      {/* MOBILE VIEW */}
      <DashboardMobileList
        reminders={followUps}
        activities={activities}
        onSelectAction={setSelectedAction}
      />

      {/* DESKTOP VIEW */}
      <div className="hidden md:flex flex-col gap-8 px-8 lg:px-12 xl:px-16 pt-14 pb-16 max-w-[1600px] w-full mx-auto">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold tracking-tight text-foreground">Home</h2>
        </div>

        <KpiSummary stats={stats} />

        <RemindersSection
          reminders={followUps}
          onSelectAction={setSelectedAction}
          onDeleteReminders={handleDeleteReminders}
        />

        <ActivitiesSection
          activities={activities}
          onDeleteActivities={handleDeleteActivities}
        />
      </div>

      <TouchpointModal
        action={selectedAction}
        onClose={() => setSelectedAction(null)}
        onSave={handleSaveTouchpoint}
      />
    </>
  );
}
