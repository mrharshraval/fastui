import { client } from "@/core/api/client";
import type {
  BusinessResponse,
  BusinessUpdateRequest,
  ActivityResponse,
  ActivityCreateRequest,
  ReminderResponse,
  ReminderCreateRequest,
  ReminderUpdateRequest,
  NoteResponse,
  NoteCreateRequest,
  DemoResponse,
  DemoCreateRequest,
  EnrichmentTriggerResponse,
  BusinessEnrichmentStatusResponse,
  OutreachResponse,
} from "@/core/api/generated";
import type { BusinessDetail, ActivityItem, ReminderItem } from "./types";
import { formatReminderDisplay } from "@/shared/lib/date";

export function formatLocation(b: BusinessResponse): string {
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

export const businessApi = {
  get: async (id: string | number): Promise<BusinessDetail> => {
    const raw = await client.get<BusinessResponse>(`/v1/businesses/${id}`);
    return {
      id: String(raw.id),
      business_name: raw.business_name || "Untitled Business",
      category: raw.category || undefined,
      address: raw.address || undefined,
      city: raw.city || undefined,
      state: raw.state || undefined,
      country: raw.country || undefined,
      location: formatLocation(raw),
      website: raw.website || undefined,
      phone: raw.phone || undefined,
      email: raw.email || undefined,
      google_maps_url: raw.google_maps_url || undefined,
      latitude: raw.latitude || undefined,
      longitude: raw.longitude || undefined,
      google_place_id: raw.google_place_id || undefined,
      created_at: raw.created_at || new Date().toISOString(),
      is_lead: raw.is_lead,
      qualification_status: raw.qualification_status || undefined,
      stage: raw.pipeline_stage ? raw.pipeline_stage.toLowerCase() : "new",
    };
  },

  update: async (id: string | number, payload: BusinessUpdateRequest): Promise<BusinessResponse> => {
    return await client.patch<BusinessResponse>(`/v1/businesses/${id}`, payload);
  },

  delete: async (id: string | number): Promise<void> => {
    await client.delete<void>(`/v1/businesses/${id}`);
  },

  promoteToLead: async (id: string | number): Promise<BusinessResponse> => {
    return await client.post<BusinessResponse>("/v1/leads", {
      business_id: Number(id),
    });
  },

  // Activities
  getActivities: async (id: string | number): Promise<ActivityItem[]> => {
    const raw = await client.get<ActivityResponse[]>(`/v1/businesses/${id}/activities`);
    return (raw || []).map((a) => ({
      id: String(a.id),
      user_name: a.user_name || "You",
      action: String(a.type || "Activity logged"),
      notes: a.notes || undefined,
      timestamp: a.created_at || new Date().toISOString(),
    }));
  },

  createActivity: async (id: string | number, payload: ActivityCreateRequest): Promise<ActivityResponse> => {
    return await client.post<ActivityResponse>(`/v1/businesses/${id}/activities`, payload);
  },

  deleteActivity: async (activityId: string | number): Promise<void> => {
    await client.delete<void>(`/v1/activities/${activityId}`);
  },

  // Notes
  createNote: async (id: string | number, content: string): Promise<NoteResponse> => {
    const payload: NoteCreateRequest = { content };
    return await client.post<NoteResponse>(`/v1/businesses/${id}/notes`, payload);
  },

  deleteNote: async (noteId: string | number): Promise<void> => {
    await client.delete<void>(`/v1/notes/${noteId}`);
  },

  // Reminders
  getReminders: async (id: string | number): Promise<ReminderItem[]> => {
    const raw = await client.get<ReminderResponse[]>(`/v1/businesses/${id}/reminders`);
    return (raw || []).map((r) => ({
      id: String(r.id),
      title: r.title || "Reminder",
      due_date: formatReminderDisplay(r.due_at),
      raw_due_at: r.due_at || undefined,
      notes: r.notes || undefined,
      status: (r.status as "pending" | "completed") || "pending",
      user_name: r.contact_name || "You",
      timestamp: r.created_at || new Date().toISOString(),
    }));
  },

  createReminder: async (id: string | number, payload: ReminderCreateRequest): Promise<ReminderResponse> => {
    return await client.post<ReminderResponse>(`/v1/businesses/${id}/reminders`, payload);
  },

  updateReminder: async (reminderId: string | number, payload: ReminderUpdateRequest): Promise<ReminderResponse> => {
    return await client.patch<ReminderResponse>(`/v1/reminders/${reminderId}`, payload);
  },

  deleteReminder: async (reminderId: string | number): Promise<void> => {
    await client.delete<void>(`/v1/reminders/${reminderId}`);
  },

  // Outreach
  logOutreach: async (
    id: string | number,
    channel: string,
    recipient: string,
    notes?: string
  ): Promise<OutreachResponse> => {
    return await client.post<OutreachResponse>(`/v1/businesses/${id}/outreach`, {
      channel,
      recipient,
      status: "completed",
      notes,
    });
  },

  // Demo
  getDemo: async (id: string | number): Promise<DemoResponse | null> => {
    return await client.get<DemoResponse>(`/v1/businesses/${id}/demo`).catch(() => null);
  },

  generateDemo: async (id: string | number, payload: DemoCreateRequest): Promise<DemoResponse> => {
    return await client.post<DemoResponse>(`/v1/businesses/${id}/demo`, payload);
  },

  // Enrichment
  triggerEnrichment: async (id: string | number): Promise<EnrichmentTriggerResponse> => {
    return await client.post<EnrichmentTriggerResponse>(`/v1/businesses/${id}/enrichment`);
  },

  getEnrichment: async (id: string | number): Promise<BusinessEnrichmentStatusResponse | null> => {
    return await client.get<BusinessEnrichmentStatusResponse>(`/v1/businesses/${id}/enrichment`).catch(() => null);
  },
};
