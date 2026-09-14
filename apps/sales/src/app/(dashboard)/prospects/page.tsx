import type { Metadata } from "next";
import { prospectsApi } from "@/features/prospects/api";
import { ProspectsView } from "@/features/prospects/ProspectsView";
import type { ProspectModel } from "@/features/prospects/types";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Prospects | Sales",
  description: "Discover and qualify prospect accounts before promoting into the sales pipeline.",
};

export default async function ProspectsPage() {
  let initialProspects: ProspectModel[] = [];
  try {
    initialProspects = await prospectsApi.list({ limit: 20 });
  } catch (err) {
    console.error("[ProspectsPage] Failed to prefetch prospects:", err);
  }

  return <ProspectsView initialProspects={initialProspects} />;
}

