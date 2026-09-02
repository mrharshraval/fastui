import { SupabaseClient } from "@supabase/supabase-js"
import { PushSubscriptionRecord } from "../types.ts"
import { logger } from "../utils/logger.ts"

export class SubscriptionRepository {
  constructor(private readonly supabase: SupabaseClient) {}

  /**
   * Batch fetches push subscriptions grouped by user ID to avoid N+1 queries.
   */
  async getSubscriptionsByUserIds(
    userIds: number[]
  ): Promise<Map<number, PushSubscriptionRecord[]>> {
    const subscriptionsByUser = new Map<number, PushSubscriptionRecord[]>()
    if (userIds.length === 0) return subscriptionsByUser

    const uniqueUserIds = [...new Set(userIds)]
    const { data, error } = await this.supabase
      .from("push_subscriptions")
      .select("id, user_id, endpoint, p256dh, auth, user_agent")
      .in("user_id", uniqueUserIds)

    if (error) {
      logger.error("subscriptions.fetch_failed", { error: error.message, userCount: uniqueUserIds.length })
      return subscriptionsByUser
    }

    if (data) {
      for (const sub of data as PushSubscriptionRecord[]) {
        const existing = subscriptionsByUser.get(sub.user_id) || []
        existing.push(sub)
        subscriptionsByUser.set(sub.user_id, existing)
      }
    }

    return subscriptionsByUser
  }

  /**
   * Prunes revoked or expired subscriptions returning HTTP 404 or 410.
   */
  async deleteSubscriptionsByEndpoints(endpoints: string[]): Promise<number> {
    if (endpoints.length === 0) return 0

    const uniqueEndpoints = [...new Set(endpoints)]
    const { error } = await this.supabase
      .from("push_subscriptions")
      .delete()
      .in("endpoint", uniqueEndpoints)

    if (error) {
      logger.error("subscriptions.delete_failed", { error: error.message, count: uniqueEndpoints.length })
      return 0
    }

    logger.info("subscriptions.expired", { prunedCount: uniqueEndpoints.length })
    return uniqueEndpoints.length
  }
}
