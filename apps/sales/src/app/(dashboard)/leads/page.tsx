import type { Metadata } from "next";
import { leadsApi } from "@/features/leads/api";
import { LeadsView } from "@/features/leads/LeadsView";
import type { LeadModel } from "@/features/leads/types";

export const metadata: Metadata = {
  title: "Leads | Sales",
  description: "Manage and track sales leads, contact channels, and conversion pipelines.",
};

export const dynamic = "force-dynamic";

export default async function LeadsPage() {
  let initialLeads: LeadModel[] = [];

  try {
    // Server-side prefetch page 0
    initialLeads = await leadsApi.list({ skip: 0, limit: 50 });
  } catch (error) {
    // Graceful fallback to client fetching if backend is unreachable at build/SSR time
    console.warn("Failed to prefetch leads on server:", error);
  }

  return <LeadsView initialLeads={initialLeads} />;
}
