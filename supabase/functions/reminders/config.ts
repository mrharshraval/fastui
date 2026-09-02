import { AppConfig } from "./types.ts"
import { ConfigError } from "./utils/errors.ts"

export function loadConfig(): AppConfig {
  const supabaseUrl = Deno.env.get("SUPABASE_URL")
  if (!supabaseUrl) {
    throw new ConfigError("Missing SUPABASE_URL environment variable")
  }

  // Parse built-in SUPABASE_SECRET_KEYS dictionary
  let secretKeysMap: Record<string, string> = {}
  try {
    const rawKeys = Deno.env.get("SUPABASE_SECRET_KEYS")
    if (rawKeys) {
      secretKeysMap = JSON.parse(rawKeys)
    }
  } catch (err: unknown) {
    console.warn("Could not parse SUPABASE_SECRET_KEYS environment variable:", err)
  }

  const legacyServiceRole = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")
  const cronSecret = Deno.env.get("CRON_SECRET")

  const defaultSecretKey =
    secretKeysMap["default"] ||
    (Object.values(secretKeysMap)[0] as string) ||
    legacyServiceRole ||
    ""

  if (!defaultSecretKey) {
    throw new ConfigError("Missing valid Secret Key configuration (SUPABASE_SECRET_KEYS['default'])")
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
    cronSecret: cronSecret || undefined,
    legacyServiceRole: legacyServiceRole || undefined,
  }
}
