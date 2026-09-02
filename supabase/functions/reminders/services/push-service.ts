import webpush from "web-push"
import { DueReminder, PushDispatchResult, PushSubscriptionRecord, VapidConfig } from "../types.ts"
import { ConfigError } from "../utils/errors.ts"
import { logger } from "../utils/logger.ts"

export class PushService {
  private initialized = false

  constructor(private readonly vapidConfig: VapidConfig) {}

  /**
   * Initializes VAPID details once.
   */
  initVapid(): void {
    if (this.initialized) return

    try {
      webpush.setVapidDetails(
        this.vapidConfig.subject,
        this.vapidConfig.publicKey,
        this.vapidConfig.privateKey
      )
      this.initialized = true
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err)
      logger.error("vapid.init_failed", { error: message })
      throw new ConfigError(`Invalid VAPID configuration: ${message}`)
    }
  }

  /**
   * Builds the Web Push notification payload for a reminder.
   */
  private buildPayload(reminder: DueReminder, businessName: string): string {
    return JSON.stringify({
      title: `Reminder: ${businessName}`,
      body: reminder.title + (reminder.notes ? ` · ${reminder.notes}` : ""),
      icon: "/assets/brand/icon/brand/primary/filled.png",
      badge: "/assets/brand/icon/brand/primary/filled.png",
      data: {
        url: "/prospects",
        business_id: reminder.business_id,
        reminder_id: reminder.id,
      },
      tag: `reminder-${reminder.id}`,
      renotify: true,
    })
  }

  /**
   * Dispatches push notifications to all registered devices for the given reminders.
   * Tracks success/failure per reminder and identifies expired endpoints (404/410).
   * Does NOT modify database state directly.
   */
  async dispatchReminders(
    reminders: DueReminder[],
    businessMap: Map<number, string>,
    subscriptionsByUser: Map<number, PushSubscriptionRecord[]>
  ): Promise<PushDispatchResult> {
    this.initVapid()

    let totalDispatched = 0
    const expiredEndpoints: string[] = []
    const deliveryPromises: Promise<void>[] = []
    const successfulReminderIds = new Set<number>()

    for (const reminder of reminders) {
      const businessName =
        reminder.business_name ||
        businessMap.get(reminder.business_id) ||
        "FastUI Sales"

      const payload = this.buildPayload(reminder, businessName)
      const userSubs = reminder.user_id ? subscriptionsByUser.get(reminder.user_id) || [] : []

      if (userSubs.length === 0) {
        logger.info("notifications.skipped", {
          reminderId: reminder.id,
          userId: reminder.user_id,
          reason: "no_registered_subscriptions",
        })
        continue
      }

      for (const sub of userSubs) {
        const pushSubscription = {
          endpoint: sub.endpoint,
          keys: {
            p256dh: sub.p256dh,
            auth: sub.auth,
          },
        }

        const task = webpush
          .sendNotification(pushSubscription, payload, { TTL: 86400 })
          .then(() => {
            totalDispatched++
            successfulReminderIds.add(reminder.id)
            logger.info("notifications.sent", {
              reminderId: reminder.id,
              userId: reminder.user_id,
              endpoint: sub.endpoint,
            })
          })
          .catch((err: unknown) => {
            const errorObj = err as { statusCode?: number; status?: number; message?: string }
            const statusCode = errorObj?.statusCode || errorObj?.status
            logger.warn("notifications.failed", {
              reminderId: reminder.id,
              endpoint: sub.endpoint,
              statusCode,
              error: errorObj?.message,
            })

            // HTTP 404 (Not Found) or 410 (Gone) indicates revoked/expired subscription
            if (statusCode === 404 || statusCode === 410) {
              expiredEndpoints.push(sub.endpoint)
            }
          })

        deliveryPromises.push(task)
      }
    }

    // Await all dispatch attempts concurrently
    await Promise.allSettled(deliveryPromises)

    const successList = Array.from(successfulReminderIds)
    const failedList = reminders
      .map((r) => r.id)
      .filter((id) => !successfulReminderIds.has(id))

    return {
      totalDispatched,
      devicesTargeted: deliveryPromises.length,
      successfulReminderIds: successList,
      failedReminderIds: failedList,
      expiredEndpoints: [...new Set(expiredEndpoints)],
    }
  }
}
