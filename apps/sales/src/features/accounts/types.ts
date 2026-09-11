export interface CompanyModel {
  id: string;
  name: string;
  domain?: string;
  industry?: string;
  status?: string;
  leads_count?: number;
}

export interface ContactModel {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  company?: string;
  role?: string;
}
