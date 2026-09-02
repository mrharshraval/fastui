import { AppConfig } from "./types.ts"
import { ConfigError } from "./utils/errors.ts"

export function loadConfig(): AppConfig {
  const supabaseUrl = Deno.env.get("SUPABASE_URL")
  if (!supabaseUrl) {
    throw new ConfigError("Missing SUPABASE_URL environment variable")
  }

  // Parse modern built-in SUPABASE_SECRET_KEYS dictionary
  let secretKeysMap: Record<string, string> = {}
  const rawKeys = Deno.env.get("SUPABASE_SECRET_KEYS")
  if (rawKeys) {
    try {
      const parsed = JSON.parse(rawKeys)
      if (Array.isArray(parsed)) {
        parsed.forEach((k, idx) => {
          if (typeof k === "string") secretKeysMap[`key_${idx}`] = k
        })
      } else if (typeof parsed === "object" && parsed !== null) {
        secretKeysMap = parsed as Record<string, string>
      } else if (typeof parsed === "string") {
        secretKeysMap["default"] = parsed
      }
    } catch {
      secretKeysMap["default"] = rawKeys.trim()
    }
  }

  const defaultSecretKey =
    secretKeysMap["default"] ||
    (Object.values(secretKeysMap)[0] as string) ||
    ""

  if (!defaultSecretKey) {
    throw new ConfigError("Missing valid Secret Key configuration in SUPABASE_SECRET_KEYS")
  }

  // VAPID configuration
  const vapidPublicKey = Deno.env.get("VAPID_PUBLIC_KEY")
  const vapidPrivateKey = Deno.env.get("VAPID_PRIVATE_KEY")
  const vapidSubject = Deno.env.get("VAPID_SUBJECT") || "mailto:notifications@fastui.in"

  if (!vapidPublicKey || !vapidPrivateKey) {
    throw new ConfigError("Missing VAPID_PUBLIC_KEY or VAPID_PRIVATE_KEY in environment secrets")
  }

  return {
    supabaseUrl,
    secretKeysMap,
    defaultSecretKey,
    vapid: {
      publicKey: vapidPublicKey,
      privateKey: vapidPrivateKey,
      subject: vapidSubject,
    },
  }
}
