export interface BusinessDetail {
  id: string;
  business_name: string;
  category?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  location?: string;
  website?: string;
  phone?: string;
  email?: string;
  whatsapp?: string;
  google_maps_url?: string;
  latitude?: number;
  longitude?: number;
  google_place_id?: string;
  created_at: string;
  is_lead?: boolean;
  qualification_status?: string;
  stage?: string;
}

export interface ActivityItem {
  id: string;
  user_name: string;
  action: string;
  notes?: string;
  timestamp: string;
}

export interface ReminderItem {
  id: string;
  title: string;
  due_date: string;
  raw_due_at?: string;
  notes?: string;
  status?: "pending" | "completed";
  user_name?: string;
  timestamp?: string;
}
