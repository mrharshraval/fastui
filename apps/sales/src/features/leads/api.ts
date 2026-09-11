import { client } from "@/core/api/client";
import type {
  BusinessResponse,
  BulkDeleteRequest,
  BulkDeleteResponse,
  BulkStageRequest,
  BulkStageResponse,
} from "@/core/api/generated";
import type { LeadFilterParams, LeadModel } from "./types";

function formatLocation(b: BusinessResponse): string {
  if (b.city && b.state && b.country) {
    if (b.city.includes(b.state) || b.city.includes(b.country)) return b.city;
    return [b.city, b.state, b.country].filter(Boolean).join(", ");
  }
  if (b.city && b.state) {
    if (b.city.includes(b.state)) return b.city;
    return `${b.city}, ${b.state}`;
  }
  return b.city || b.address || b.country || "—";
}

export function mapBusinessToLead(b: BusinessResponse): LeadModel {
  return {
    id: String(b.id),
    business_name: b.business_name || "Untitled Lead",
    location: formatLocation(b),
    website: b.website || undefined,
    phone: b.phone || undefined,
    email: b.email || undefined,
    whatsapp: b.phone
      ? (() => {
          const digits = b.phone.replace(/[^0-9]/g, "");
          const clean = digits.startsWith("0") && digits.length === 11 ? digits.slice(1) : digits;
          return clean.length === 10 ? `91${clean}` : clean;
        })()
      : undefined,
    status: b.pipeline_stage ? b.pipeline_stage.toLowerCase() : "new",
    priority: b.priority || "medium",
    signal: b.signal || "warm",
    owner: "me",
    source: "discover",
    follow_up: "None",
    created_at: b.created_at || new Date().toISOString(),
  };
}

/**
 * Domain-level API functions for Leads.
 * Consumes the frozen backend endpoints directly: GET /v1/leads, PATCH /v1/leads, DELETE /v1/businesses.
 */
export const leadsApi = {
  list: async (params?: LeadFilterParams, signal?: AbortSignal): Promise<LeadModel[]> => {
    const raw = await client.get<BusinessResponse[]>("/v1/leads", {
      params: {
        skip: params?.skip ?? 0,
        limit: params?.limit ?? 50,
        stage: params?.stage,
        search: params?.search,
        sort_by: params?.sort_by ?? "created_at",
        sort_order: params?.sort_order ?? "desc",
      },
      signal,
    });
    return (raw || []).map(mapBusinessToLead);
  },

  updateBulkStage: async (businessIds: number[], stage: string): Promise<BulkStageResponse> => {
    const payload: BulkStageRequest = {
      business_ids: businessIds,
      stage,
    };
    return await client.patch<BulkStageResponse>("/v1/leads", payload);
  },

  updateStage: async (businessId: number, stage: string): Promise<BusinessResponse> => {
    return await client.patch<BusinessResponse>(`/v1/businesses/${businessId}`, {
      pipeline_stage: stage,
    });
  },

  deleteBulk: async (businessIds: number[]): Promise<BulkDeleteResponse> => {
    const payload: BulkDeleteRequest = {
      business_ids: businessIds,
    };
    return await client.delete<BulkDeleteResponse>("/v1/businesses", {
      body: payload,
    });
  },

  deleteSingle: async (businessId: number): Promise<void> => {
    await client.delete<void>(`/v1/businesses/${businessId}`);
  },

  logActivity: async (
    businessId: number,
    payload: { type: string; channel?: string; outcome?: string; notes?: string }
  ): Promise<void> => {
    await client.post(`/v1/businesses/${businessId}/activities`, payload);
  },
};
