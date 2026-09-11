export interface ProspectModel {
  id: string;
  business_name: string;
  location?: string;
  website?: string;
  phone?: string;
  email?: string;
  whatsapp?: string;
  qualification_status: string; // "unqualified" | "reviewing" | "qualified" | "disqualified"
  source?: string;
  created_at: string;
}

export interface ProspectFilterParams {
  skip?: number;
  limit?: number;
  qualification_status?: string;
  search?: string;
  sort_by?: string;
  sort_order?: string;
}
