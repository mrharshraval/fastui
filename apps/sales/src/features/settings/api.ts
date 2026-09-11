import { client } from "@/core/api/client";
import type {
  TokenData,
  UserProfileUpdateRequest,
  PasswordUpdateRequest,
} from "@/core/api/generated";

export const settingsApi = {
  getCurrentUser: async (): Promise<TokenData> => {
    return await client.get<TokenData>("/v1/auth/me");
  },

  updateProfile: async (payload: UserProfileUpdateRequest): Promise<TokenData> => {
    return await client.patch<TokenData>("/v1/auth/me", payload);
  },

  updatePassword: async (payload: PasswordUpdateRequest): Promise<{ message: string }> => {
    return await client.put<{ message: string }>("/v1/auth/password", payload);
  },

  deleteAccount: async (): Promise<void> => {
    await client.delete<void>("/v1/auth/me");
  },

  logout: async (): Promise<void> => {
    await client.post<void>("/v1/auth/logout");
  },
};
