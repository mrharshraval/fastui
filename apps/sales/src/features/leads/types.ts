export interface LeadModel {
  id: string;
  business_name: string;
  location?: string;
  website?: string;
  phone?: string;
  email?: string;
  whatsapp?: string;
  status: string;
  priority?: string;
  signal?: string;
  owner?: string;
  source?: string;
  follow_up?: string;
  created_at: string;
}

export interface LeadFilterParams {
  skip?: number;
  limit?: number;
  stage?: string;
  search?: string;
  sort_by?: string;
  sort_order?: string;
}
