export interface PushSubscriptionRecord {
  id: number
  user_id: number
  endpoint: string
  p256dh: string
  auth: string
  user_agent?: string
}

export interface DueReminder {
  id: number
  business_id: number
  user_id: number | null
  title: string
  notes: string | null
  due_at: string
  business_name?: string
}

export interface PushDispatchResult {
  totalDispatched: number
  devicesTargeted: number
  successfulReminderIds: number[]
  failedReminderIds: number[]
  expiredEndpoints: string[]
}

export interface ProcessingSummary {
  success: boolean
  reminders_claimed: number
  reminders_notified: number
  reminders_unnotified: number
  notifications_sent: number
  devices_targeted: number
  stale_subscriptions_cleaned: number
  duration_ms: number
}

export interface VapidConfig {
  publicKey: string
  privateKey: string
  subject: string
}

export interface AppConfig {
  supabaseUrl: string
  secretKeysMap: Record<string, string>
  defaultSecretKey: string
  vapid: VapidConfig
  cronSecret?: string
  legacyServiceRole?: string
}
