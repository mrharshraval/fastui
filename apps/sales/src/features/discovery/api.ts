import { client } from "@/core/api/client";
import type {
  JobCreateResponse,
  JobStatusResponse,
  ProspectingQuery,
} from "@/core/api/generated";

export const discoveryApi = {
  createJob: async (query: ProspectingQuery): Promise<JobCreateResponse> => {
    return await client.post<JobCreateResponse>("/v1/prospecting/jobs", query);
  },

  getJobStatus: async (jobId: string | number): Promise<JobStatusResponse> => {
    return await client.get<JobStatusResponse>(`/v1/prospecting/jobs/${jobId}`);
  },

  cancelJob: async (jobId: string | number): Promise<void> => {
    await client.post<void>(`/v1/prospecting/jobs/${jobId}/cancel`);
  },
};
