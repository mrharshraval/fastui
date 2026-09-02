import { SupabaseClient } from "@supabase/supabase-js"
import { DueReminder } from "../types.ts"
import { logger } from "../utils/logger.ts"

export class ReminderRepository {
  constructor(private readonly supabase: SupabaseClient) {}

  /**
   * Atomically claims due reminders using the claim_due_reminders RPC.
   * Acquires a 5-minute processing lease (notification_processing_at = NOW())
   * with FOR UPDATE SKIP LOCKED to prevent duplicate processing across concurrent workers.
   */
  async claimDueReminders(batchLimit: number = 50): Promise<DueReminder[]> {
    const { data: rpcData, error: rpcError } = await this.supabase.rpc("claim_due_reminders", {
      batch_limit: batchLimit,
    })

    if (!rpcError && Array.isArray(rpcData)) {
      return rpcData as DueReminder[]
    }

    // Isolated fallback: Only used if the stored procedure has not yet been applied
    logger.warn("reminders.rpc_fallback", {
      reason: "RPC claim_due_reminders not available; using query fallback",
      error: rpcError?.message,
    })

    const now = new Date().toISOString()
    const fiveMinAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString()

    const { data: selectData, error: selectError } = await this.supabase
      .from("reminders")
      .select("id, business_id, user_id, title, notes, due_at")
      .in("status", ["PENDING", "pending"])
      .lte("due_at", now)
      .is("notification_sent_at", null)
      .or(`notification_processing_at.is.null,notification_processing_at.lte.${fiveMinAgo}`)
      .order("due_at", { ascending: true })
      .limit(batchLimit)

    if (selectError) {
      logger.error("reminders.select_failed", { error: selectError.message })
      throw new Error(`Database query failed: ${selectError.message}`)
    }

    if (!selectData || selectData.length === 0) {
      return []
    }

    const ids = selectData.map((r) => r.id)
    const { error: leaseError } = await this.supabase
      .from("reminders")
      .update({ notification_processing_at: now, updated_at: now })
      .in("id", ids)

    if (leaseError) {
      logger.error("reminders.lease_failed", { error: leaseError.message })
      throw new Error(`Failed to acquire processing lease: ${leaseError.message}`)
    }

    return selectData as DueReminder[]
  }

  /**
   * Marks reminders as successfully sent and clears their processing lease.
   * ONLY called when Web Push delivery has succeeded.
   */
  async markRemindersSent(ids: number[]): Promise<void> {
    if (ids.length === 0) return

    const now = new Date().toISOString()
    const { error } = await this.supabase
      .from("reminders")
      .update({
        notification_sent_at: now,
        notification_processing_at: null,
        updated_at: now,
      })
      .in("id", ids)

    if (error) {
      logger.error("reminders.mark_sent_failed", { error: error.message, count: ids.length })
      throw new Error(`Failed to mark reminders as sent: ${error.message}`)
    }
  }

  /**
   * Releases the temporary processing lease for reminders whose notifications
   * could not be delivered (e.g. no active subscriptions or push endpoint failures).
   * Does NOT mark notification_sent_at.
   */
  async releaseRemindersLease(ids: number[]): Promise<void> {
    if (ids.length === 0) return

    const now = new Date().toISOString()
    const { error } = await this.supabase
      .from("reminders")
      .update({
        notification_processing_at: null,
        updated_at: now,
      })
      .in("id", ids)

    if (error) {
      logger.error("reminders.release_lease_failed", { error: error.message, count: ids.length })
    }
  }
}
