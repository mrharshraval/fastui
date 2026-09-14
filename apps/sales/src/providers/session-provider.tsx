"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  useEffect,
} from "react";
import type { TokenData } from "@/core/api/generated";

export interface SessionContextValue {
  session: TokenData | null;
  /** Convenient alias for session */
  user: TokenData | null;
  /** Updates the in-memory session state (e.g. after a profile update) */
  updateSession: (updated: Partial<TokenData> | TokenData) => void;
  /** Immediately wipes client in-memory session (e.g. on logout or account deletion) */
  clearSession: () => void;
}

const defaultContextValue: SessionContextValue = {
  session: null,
  user: null,
  updateSession: () => {},
  clearSession: () => {},
};

const SessionContext = createContext<SessionContextValue>(defaultContextValue);

export interface SessionProviderProps {
  session: TokenData | null;
  children: React.ReactNode;
}

/**
 * SessionProvider acts strictly as a distribution mechanism for an already
 * server-resolved session. It never calls /v1/auth/me or performs client-side
 * network fetches on mount or navigation.
 */
export function SessionProvider({ session: initialSession, children }: SessionProviderProps) {
  const [session, setSession] = useState<TokenData | null>(initialSession);

  // Sync if parent RSC resolves a new session (e.g., revalidation or user switch)
  useEffect(() => {
    setSession(initialSession);
  }, [initialSession]);

  const updateSession = useCallback((updated: Partial<TokenData> | TokenData) => {
    setSession((prev) => {
      if (!prev) return (updated as TokenData) ?? null;
      return { ...prev, ...updated };
    });
  }, []);

  const clearSession = useCallback(() => {
    setSession(null);
  }, []);

  const value = useMemo<SessionContextValue>(
    () => ({
      session,
      user: session,
      updateSession,
      clearSession,
    }),
    [session, updateSession, clearSession]
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

/**
 * Hook to consume the distributed session in Client Components.
 * Never triggers a client /v1/auth/me request.
 */
export function useSession(): SessionContextValue {
  const context = useContext(SessionContext);
  return context ?? defaultContextValue;
}
