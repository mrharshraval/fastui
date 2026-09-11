import { Suspense } from "react";
import { dashboardApi } from "@/features/dashboard/api";
import { DashboardView } from "@/features/dashboard/DashboardView";
import { formatReminderDisplay, getReminderUrgency } from "@/shared/lib/date";
import type { StatsModel, FollowUpAction, ActivityFeedModel } from "@/features/dashboard/types";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let stats: StatsModel = {
    total_leads: 0,
    pipeline_value: 0,
    active_companies: 0,
    conversion_rate: 0,
  };
  let activities: ActivityFeedModel[] = [];
  let followUps: FollowUpAction[] = [];

  try {
    const [statsRes, remindersRes] = await Promise.all([
      dashboardApi.getStats().catch(() => null),
      dashboardApi.getReminders().catch(() => null),
    ]);

    if (statsRes) {
      stats = {
        total_leads: statsRes.new_leads ?? 0,
        pipeline_value: statsRes.proposals_sent ? statsRes.proposals_sent * 45000 : 0,
        active_companies: statsRes.follow_ups ? statsRes.follow_ups * 12 : 0,
        conversion_rate: 0,
      };

      if (Array.isArray(statsRes.recent_activities)) {
        activities = statsRes.recent_activities.map((a, idx) => ({
          id: `act-live-${idx}`,
          action: a.outcome || a.notes || "Activity logged",
          type: a.type?.includes("call") ? "calls" : "emails",
          lead: a.target || "Business Activity",
          company: "Client",
          time: a.time || "Recently",
        }));
      }
    }

    if (Array.isArray(remindersRes)) {
      followUps = remindersRes.map((f) => ({
        id: String(f.id),
        contactName: f.contact_name || f.title || "Contact",
        company: "Company",
        lastInteraction: f.notes || f.title || "Pending touchpoint",
        nextAction: f.notes || f.title || "Follow up",
        dueDate: f.due_at ? formatReminderDisplay(f.due_at) : "Upcoming",
        bucket: getReminderUrgency(f.due_at),
        done: f.status?.toLowerCase() === "completed" || f.status?.toLowerCase() === "done",
      }));
    }
  } catch (err) {
    console.error("[DashboardPage] SSR prefetch failed:", err);
  }

  return (
    <Suspense fallback={null}>
      <DashboardView
        initialStats={stats}
        initialFollowUps={followUps}
        initialActivities={activities}
      />
    </Suspense>
  );
}
