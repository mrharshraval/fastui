import { businessApi } from "@/features/businesses/api";
import { BusinessView } from "@/features/businesses/BusinessView";
import type { BusinessDetail, ActivityItem, ReminderItem } from "@/features/businesses/types";
import type { Metadata } from "next";

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  try {
    const business = await businessApi.get(id);
    return {
      title: `${business.business_name} | Sales`,
      description: `View profile, activity, reminders, and engagement details for ${business.business_name}.`,
    };
  } catch {
    return {
      title: "Business Profile | Sales",
      description: "View business profile details.",
    };
  }
}

export default async function BusinessProfilePage({ params }: PageProps) {
  const { id } = await params;
  let business: BusinessDetail | null = null;
  let activities: ActivityItem[] = [];
  let reminders: ReminderItem[] = [];

  try {
    // Parallel prefetch on server
    const [bRes, aRes, rRes] = await Promise.allSettled([
      businessApi.get(id),
      businessApi.getActivities(id),
      businessApi.getReminders(id),
    ]);

    if (bRes.status === "fulfilled") {
      business = bRes.value;
    }
    if (aRes.status === "fulfilled") {
      activities = aRes.value;
    }
    if (rRes.status === "fulfilled") {
      reminders = rRes.value;
    }
  } catch (error) {
    console.warn("Failed to prefetch business data on server:", error);
  }

  return (
    <BusinessView
      initialBusiness={business}
      initialActivities={activities}
      initialReminders={reminders}
    />
  );
}
