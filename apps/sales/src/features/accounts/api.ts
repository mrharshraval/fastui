import { client } from "@/core/api/client";
import type { BusinessResponse, ContactResponse } from "@/core/api/generated";
import type { CompanyModel, ContactModel } from "./types";

export const accountsApi = {
  listCompanies: async (params?: { skip?: number; limit?: number; search?: string }): Promise<CompanyModel[]> => {
    const raw = await client.get<BusinessResponse[]>("/v1/businesses", {
      params: {
        skip: params?.skip ?? 0,
        limit: params?.limit ?? 100,
        search: params?.search,
      },
    });

    return (raw || []).map((b) => ({
      id: String(b.id),
      name: b.business_name || "Untitled",
      domain: b.website ? b.website.replace(/^https?:\/\//, "").replace(/\/$/, "") : undefined,
      industry: b.category || "General",
      leads_count: b.is_lead ? 1 : 0,
    }));
  },

  listContacts: async (params?: { skip?: number; limit?: number; search?: string }): Promise<ContactModel[]> => {
    const raw = await client.get<ContactResponse[]>("/v1/contacts", {
      params: {
        skip: params?.skip ?? 0,
        limit: params?.limit ?? 100,
        search: params?.search,
      },
    });

    return (raw || []).map((c) => ({
      id: String(c.id),
      name: c.name || "Unnamed",
      email: c.email || undefined,
      phone: c.phone || undefined,
      company: "Account",
      role: c.role || "Contact",
    }));
  },

  deleteCompany: async (id: string | number): Promise<void> => {
    await client.delete<void>(`/v1/businesses/${id}`);
  },

  deleteContact: async (id: string | number): Promise<void> => {
    await client.delete<void>(`/v1/contacts/${id}`);
  },
};
