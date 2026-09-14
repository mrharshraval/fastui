import { client } from "@/core/api/client";
import type { RequestOptions } from "@/core/api/client";
import type {
  DashboardStatsResponse,
  ReminderResponse,
  ReminderUpdateRequest,
} from "@/core/api/generated";

export const dashboardApi = {
  getStats: async (options?: Pick<RequestOptions, "cache" | "next">): Promise<DashboardStatsResponse> => {
    return await client.get<DashboardStatsResponse>("/v1/stats", options);
  },

  getReminders: async (options?: Pick<RequestOptions, "cache" | "next">): Promise<ReminderResponse[]> => {
    return await client.get<ReminderResponse[]>("/v1/reminders", options);
  },

  updateReminder: async (
    reminderId: string | number,
    payload: ReminderUpdateRequest
  ): Promise<ReminderResponse> => {
    return await client.patch<ReminderResponse>(`/v1/reminders/${reminderId}`, payload);
  },

  deleteReminder: async (reminderId: string | number): Promise<void> => {
    await client.delete<void>(`/v1/reminders/${reminderId}`);
  },
};
