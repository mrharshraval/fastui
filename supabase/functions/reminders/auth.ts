import { AppConfig } from "./types.ts"
import { UnauthorizedError } from "./utils/errors.ts"

export interface AuthResult {
  isAuthorized: boolean
  callerKey: string
}

function isValidWorkerKey(callerKey: string, validSecretKeys: string[]): boolean {
  // 1. Match against configured SUPABASE_SECRET_KEYS / SUPABASE_SERVICE_ROLE_KEY
  if (validSecretKeys.length > 0 && validSecretKeys.includes(callerKey)) {
    return true
  }

  // 2. Validate Supabase service_role / anon key token from Supabase Vault
  try {
    const parts = callerKey.split(".")
    if (parts.length === 3) {
      const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/")
      const decoded = atob(base64)
      const payload = JSON.parse(decoded)
      if (
        payload &&
        (payload.role === "service_role" || payload.role === "anon") &&
        payload.iss === "supabase"
      ) {
        return true
      }
    }
  } catch {
    // Fallthrough on invalid JWT
  }

  return false
}

export function authenticateWorker(req: Request, config: AppConfig): AuthResult {
  const incomingApiKey =
    req.headers.get("apikey") ||
    req.headers.get("Authorization")?.replace(/^Bearer\s+/i, "")

  const callerKey = incomingApiKey?.trim()
  if (!callerKey) {
    throw new UnauthorizedError("Missing apikey or Authorization header")
  }

  // Collect valid authorized secret keys
  const validSecretKeys: string[] = Object.values(config.secretKeysMap).filter(
    (k): k is string => Boolean(k) && typeof k === "string"
  )

  const isAuthorized = isValidWorkerKey(callerKey, validSecretKeys)

  if (!isAuthorized) {
    throw new UnauthorizedError("Invalid or unauthorized Secret Key")
  }

  return {
    isAuthorized: true,
    callerKey,
  }
}
