import { client } from "@/core/api/client";
import type { PipelineDealResponse, BusinessResponse } from "@/core/api/generated";

export interface DealModel {
  id: string;
  business_name: string;
  value?: number;
  stage: string;
  probability?: number;
}

export const pipelineApi = {
  list: async (): Promise<DealModel[]> => {
    const raw = await client.get<PipelineDealResponse[]>("/v1/pipeline");
    return (raw || []).map((d) => ({
      id: String(d.id),
      business_name: d.business_name || "Untitled Deal",
      value: d.value ?? undefined,
      stage: d.stage || "Qualification",
      probability: d.probability ?? undefined,
    }));
  },

  updateStage: async (businessId: number, stage: string): Promise<BusinessResponse> => {
    return await client.patch<BusinessResponse>(`/v1/businesses/${businessId}`, {
      pipeline_stage: stage,
    });
  },

  delete: async (businessId: number): Promise<void> => {
    await client.delete<void>(`/v1/businesses/${businessId}`);
  },
};
