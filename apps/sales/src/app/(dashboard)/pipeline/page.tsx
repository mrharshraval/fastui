import { Suspense } from "react";
import { pipelineApi, type DealModel } from "@/features/pipeline/api";
import { PipelineView } from "@/features/pipeline/PipelineView";

export const dynamic = "force-dynamic";

export default async function PipelinePage() {
  let initialDeals: DealModel[] = [];
  try {
    initialDeals = await pipelineApi.list();
  } catch (err) {
    console.error("[PipelinePage] SSR prefetch failed:", err);
  }

  return (
    <Suspense fallback={null}>
      <PipelineView initialDeals={initialDeals} />
    </Suspense>
  );
}
