import type { Metadata } from "next";
import { prospectsApi } from "@/features/prospects/api";
import { ProspectsView } from "@/features/prospects/ProspectsView";
import type { ProspectModel } from "@/features/prospects/types";

export const metadata: Metadata = {
  title: "Prospects | Sales",
  description: "Discover and qualify prospect accounts before promoting into the sales pipeline.",
};

export const dynamic = "force-dynamic";

export default async function ProspectsPage() {
  let initialProspects: ProspectModel[] = [];

  try {
    initialProspects = await prospectsApi.list({ skip: 0, limit: 50 });
  } catch (error) {
    console.warn("Failed to prefetch prospects on server:", error);
  }

  return <ProspectsView initialProspects={initialProspects} />;
}
