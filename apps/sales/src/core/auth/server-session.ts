import "server-only";

import { cache } from "react";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { authApi } from "@/features/auth/api";
import type { TokenData } from "@/core/api/generated";

/**
 * Resolves the authenticated session on the server for the current request tree.
 * Wrapped in React.cache for request-level memoization so multiple server consumers
 * incur at most one backend /v1/auth/me identity verification per request.
 *
 * Returns null if unauthenticated or if the token is invalid/expired.
 */
export const getSession = cache(async (): Promise<TokenData | null> => {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("access_token")?.value;
    if (!token) {
      return null;
    }

    return await authApi.getMe();
  } catch (error: any) {
    if (error?.digest?.startsWith?.("NEXT_REDIRECT")) {
      throw error;
    }
    return null;
  }
});

/**
 * Authoritative server-side session gate for protected RSC trees.
 * Resolves the authenticated user via backend cryptographic JWT verification.
 * If the session is missing or the backend responds with 401 (e.g., token expired,
 * revoked, or tampered), immediately redirects to /login on the server rather than
 * rendering an unauthenticated or blank shell.
 */
export const requireSession = cache(async (returnUrl?: string): Promise<TokenData> => {
  const loginDestination = returnUrl
    ? `/login?returnUrl=${encodeURIComponent(returnUrl)}`
    : "/login";

  try {
    const cookieStore = await cookies();
    const token = cookieStore.get("access_token")?.value;
    if (!token) {
      redirect(loginDestination);
    }

    const session = await authApi.getMe();
    if (!session || !session.email) {
      redirect(loginDestination);
    }

    return session;
  } catch (error: any) {
    if (error?.digest?.startsWith?.("NEXT_REDIRECT")) {
      throw error;
    }

    // 401 Unauthorized from backend -> immediate server redirect
    if (error?.status === 401) {
      redirect(loginDestination);
    }

    // Rethrow server errors or unexpected issues
    throw error;
  }
});
