import { ReminderRepository } from "../repositories/reminder-repository.ts"
import { BusinessRepository } from "../repositories/business-repository.ts"
import { SubscriptionRepository } from "../repositories/subscription-repository.ts"
import { PushService } from "./push-service.ts"
import { ProcessingSummary } from "../types.ts"
import { logger } from "../utils/logger.ts"

export class ReminderService {
  constructor(
    private readonly reminderRepo: ReminderRepository,
    private readonly businessRepo: BusinessRepository,
    private readonly subscriptionRepo: SubscriptionRepository,
    private readonly pushService: PushService
  ) {}

  /**
   * Orchestrates the complete reminder processing cycle:
   * 1. Atomically claims due reminders (5-minute lease)
   * 2. Batch loads business & subscription data (no N+1)
   * 3. Dispatches push notifications to all registered devices
   * 4. Stamps notification_sent_at ONLY on successful delivery
   * 5. Releases lease for failed/unregistered reminders
   * 6. Purges expired/unsubscribed push endpoints
   */
  async processDueReminders(batchLimit: number = 50): Promise<ProcessingSummary> {
    const startTime = Date.now()

    // 1. Claim due reminders
    const dueReminders = await this.reminderRepo.claimDueReminders(batchLimit)

    if (dueReminders.length === 0) {
      return {
        success: true,
        reminders_claimed: 0,
        reminders_notified: 0,
        reminders_unnotified: 0,
        notifications_sent: 0,
        devices_targeted: 0,
        stale_subscriptions_cleaned: 0,
        duration_ms: Date.now() - startTime,
      }
    }

    logger.info("reminders.claimed", { count: dueReminders.length })

    // 2. Batch load business names for reminders lacking denormalized business_name
    const missingBusinessIds = [
      ...new Set(
        dueReminders
          .filter((r) => !r.business_name && r.business_id)
          .map((r) => r.business_id)
      ),
    ]
    const businessMap = await this.businessRepo.getBusinessNamesByIds(missingBusinessIds)

    // 3. Batch load push subscriptions for target users
    const targetUserIds = [
      ...new Set(
        dueReminders
          .map((r) => r.user_id)
          .filter((uid): uid is number => uid !== null)
      ),
    ]
    const subscriptionsByUser = await this.subscriptionRepo.getSubscriptionsByUserIds(targetUserIds)

    // 4. Dispatch push notifications with failure isolation
    const dispatchResult = await this.pushService.dispatchReminders(
      dueReminders,
      businessMap,
      subscriptionsByUser
    )

    // 5. Update reminder states:
    // A. Mark successfully notified reminders (clears lease + stamps notification_sent_at)
    if (dispatchResult.successfulReminderIds.length > 0) {
      await this.reminderRepo.markRemindersSent(dispatchResult.successfulReminderIds)
    }

    // B. Release lease on reminders that could not be delivered (clears lease, leaves notification_sent_at as NULL)
    if (dispatchResult.failedReminderIds.length > 0) {
      await this.reminderRepo.releaseRemindersLease(dispatchResult.failedReminderIds)
    }

    // 6. Purge dead subscriptions (404/410)
    let prunedCount = 0
    if (dispatchResult.expiredEndpoints.length > 0) {
      prunedCount = await this.subscriptionRepo.deleteSubscriptionsByEndpoints(
        dispatchResult.expiredEndpoints
      )
    }

    const summary: ProcessingSummary = {
      success: true,
      reminders_claimed: dueReminders.length,
      reminders_notified: dispatchResult.successfulReminderIds.length,
      reminders_unnotified: dispatchResult.failedReminderIds.length,
      notifications_sent: dispatchResult.totalDispatched,
      devices_targeted: dispatchResult.devicesTargeted,
      stale_subscriptions_cleaned: prunedCount,
      duration_ms: Date.now() - startTime,
    }

    logger.info("reminders.completed", summary)
    return summary
  }
}
