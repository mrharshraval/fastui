import type { Metadata } from "next";
import { leadsApi } from "@/features/leads/api";
import { LeadsView } from "@/features/leads/LeadsView";
import type { LeadModel } from "@/features/leads/types";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Leads | Sales",
  description: "Manage and track sales leads, contact channels, and conversion pipelines.",
};

export default async function LeadsPage() {
  let initialLeads: LeadModel[] = [];
  try {
    initialLeads = await leadsApi.list({ limit: 20 });
  } catch (err) {
    console.error("[LeadsPage] Failed to prefetch leads:", err);
  }

  return <LeadsView initialLeads={initialLeads} />;
}

