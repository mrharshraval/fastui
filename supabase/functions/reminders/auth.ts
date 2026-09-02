import { AppConfig } from "./types.ts"
import { UnauthorizedError } from "./utils/errors.ts"

export interface AuthResult {
  isAuthorized: boolean
  callerKey: string
}

export function authenticateWorker(req: Request, config: AppConfig): AuthResult {
  const incomingApiKey =
    req.headers.get("apikey") ||
    req.headers.get("Authorization")?.replace(/^Bearer\s+/i, "")

  const callerKey = incomingApiKey?.trim()
  if (!callerKey) {
    throw new UnauthorizedError("Missing apikey or Authorization header")
  }

  // Collect valid authorized keys
  const validSecretKeys: string[] = Object.values(config.secretKeysMap).filter(
    (k): k is string => Boolean(k) && typeof k === "string"
  )

  // Backward-compatibility fallbacks
  if (config.cronSecret) validSecretKeys.push(config.cronSecret)
  if (config.legacyServiceRole) validSecretKeys.push(config.legacyServiceRole)

  const isAuthorized = validSecretKeys.length > 0 && validSecretKeys.includes(callerKey)

  if (!isAuthorized) {
    throw new UnauthorizedError()
  }

  return {
    isAuthorized: true,
    callerKey,
  }
}
