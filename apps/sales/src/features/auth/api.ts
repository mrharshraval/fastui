import { client } from "@/core/api/client";
import type {
  RegisterRequest,
  TokenResponse,
  VerifyOTPRequest,
  LoginRequest,
  PasswordResetRequest,
  PasswordResetConfirm,
  TokenData,
} from "@/core/api/generated";

export const authApi = {
  register: async (payload: RegisterRequest): Promise<TokenResponse> => {
    return await client.post<TokenResponse>("/v1/auth/register", payload);
  },

  verifyOtp: async (payload: VerifyOTPRequest): Promise<TokenResponse> => {
    return await client.post<TokenResponse>("/v1/auth/verify", payload);
  },

  login: async (payload: LoginRequest): Promise<TokenResponse> => {
    return await client.post<TokenResponse>("/v1/auth/login", payload);
  },

  logout: async (): Promise<void> => {
    await client.post<void>("/v1/auth/logout");
  },

  getMe: async (): Promise<TokenData> => {
    return await client.get<TokenData>("/v1/auth/me");
  },

  requestPasswordReset: async (payload: PasswordResetRequest): Promise<{ message: string }> => {
    return await client.post<{ message: string }>("/v1/auth/password/reset/request", payload);
  },

  confirmPasswordReset: async (payload: PasswordResetConfirm): Promise<{ message: string }> => {
    return await client.post<{ message: string }>("/v1/auth/password/reset/confirm", payload);
  },
};
