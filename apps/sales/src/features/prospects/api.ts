import { client } from "@/core/api/client";
import type {
  BusinessResponse,
  BulkQualifyRequest,
  BulkQualifyResponse,
  BulkDeleteRequest,
  BulkDeleteResponse,
  QualifyProspectRequest,
  BulkAddToLeadsResponse,
} from "@/core/api/generated";
import type { ProspectFilterParams, ProspectModel } from "./types";

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

export function mapBusinessToProspect(b: BusinessResponse): ProspectModel {
  return {
    id: String(b.id),
    business_name: b.business_name || "Untitled Prospect",
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
    qualification_status: b.qualification_status ? b.qualification_status.toLowerCase() : "unqualified",
    source: "discover",
    created_at: b.created_at || new Date().toISOString(),
  };
}

/**
 * Domain-level API functions for Prospects.
 * Consumes the frozen backend endpoints directly: GET /v1/prospects, PATCH /v1/prospects, PATCH /v1/prospects/{id}.
 */
export const prospectsApi = {
  list: async (params?: ProspectFilterParams, signal?: AbortSignal): Promise<ProspectModel[]> => {
    const raw = await client.get<BusinessResponse[]>("/v1/prospects", {
      params: {
        skip: params?.skip ?? 0,
        limit: params?.limit ?? 50,
        qualification_status: params?.qualification_status,
        search: params?.search,
        sort_by: params?.sort_by ?? "created_at",
        sort_order: params?.sort_order ?? "desc",
      },
      signal,
    });
    return (raw || []).map(mapBusinessToProspect);
  },

  updateBulkQualification: async (
    businessIds: number[],
    qualificationStatus: string
  ): Promise<BulkQualifyResponse> => {
    const payload: BulkQualifyRequest = {
      business_ids: businessIds,
      qualification_status: qualificationStatus,
    };
    return await client.patch<BulkQualifyResponse>("/v1/prospects", payload);
  },

  qualifySingle: async (
    businessId: number,
    qualificationStatus: string
  ): Promise<BusinessResponse> => {
    const payload: QualifyProspectRequest = {
      qualification_status: qualificationStatus,
    };
    return await client.patch<BusinessResponse>(`/v1/prospects/${businessId}`, payload);
  },

  promoteToLeads: async (
    businessIds: number[]
  ): Promise<BusinessResponse | BulkAddToLeadsResponse> => {
    if (businessIds.length === 1) {
      return await client.post<BusinessResponse>("/v1/leads", {
        business_id: businessIds[0],
      });
    }
    return await client.post<BulkAddToLeadsResponse>("/v1/leads", {
      business_ids: businessIds,
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

  logOutreach: async (
    businessId: number,
    payload: { channel: string; recipient: string; status?: string; notes?: string }
  ): Promise<void> => {
    await client.post(`/v1/businesses/${businessId}/outreach`, payload);
  },
};
