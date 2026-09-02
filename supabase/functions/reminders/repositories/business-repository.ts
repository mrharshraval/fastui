import { SupabaseClient } from "@supabase/supabase-js"
import { logger } from "../utils/logger.ts"

export class BusinessRepository {
  constructor(private readonly supabase: SupabaseClient) {}

  /**
   * Batch fetches business names by IDs to avoid N+1 queries.
   */
  async getBusinessNamesByIds(businessIds: number[]): Promise<Map<number, string>> {
    const businessMap = new Map<number, string>()
    if (businessIds.length === 0) return businessMap

    const uniqueIds = [...new Set(businessIds)]
    const { data, error } = await this.supabase
      .from("businesses")
      .select("id, business_name")
      .in("id", uniqueIds)

    if (error) {
      logger.warn("businesses.fetch_failed", { error: error.message, count: uniqueIds.length })
      return businessMap
    }

    if (data) {
      for (const row of data) {
        businessMap.set(row.id, row.business_name)
      }
    }

    return businessMap
  }
}
