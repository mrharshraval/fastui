import { createClient } from "@supabase/supabase-js"
import { loadConfig } from "./config.ts"
import { authenticateWorker } from "./auth.ts"
import { ReminderRepository } from "./repositories/reminder-repository.ts"
import { BusinessRepository } from "./repositories/business-repository.ts"
import { SubscriptionRepository } from "./repositories/subscription-repository.ts"
import { PushService } from "./services/push-service.ts"
import { ReminderService } from "./services/reminder-service.ts"
import { AppError, MethodNotAllowedError } from "./utils/errors.ts"
import { jsonResponse, errorResponse } from "./utils/response.ts"
import { logger } from "./utils/logger.ts"

/**
 * Handles incoming HTTP requests for the reminders Edge Function.
 * Orchestrates method validation, authentication, service invocation, and error mapping.
 */
export async function handleReminders(req: Request): Promise<Response> {
  try {
    // 1. Validate HTTP method
    if (req.method !== "POST" && req.method !== "GET") {
      throw new MethodNotAllowedError()
    }

    // 2. Load configuration & authenticate request
    const config = loadConfig()
    const authResult = authenticateWorker(req, config)

    // 3. Initialize admin database client (bypasses RLS for worker processing)
    const adminKey = config.defaultSecretKey || authResult.callerKey
    const supabase = createClient(config.supabaseUrl, adminKey, {
      auth: { persistSession: false },
    })

    // 4. Construct layered dependencies
    const reminderRepo = new ReminderRepository(supabase)
    const businessRepo = new BusinessRepository(supabase)
    const subscriptionRepo = new SubscriptionRepository(supabase)
    const pushService = new PushService(config.vapid)

    const reminderService = new ReminderService(
      reminderRepo,
      businessRepo,
      subscriptionRepo,
      pushService
    )

    // 5. Execute reminder processing cycle
    const result = await reminderService.processDueReminders(50)
    return jsonResponse(result, 200)
  } catch (err: unknown) {
    if (err instanceof AppError) {
      logger.warn("request.rejected", {
        errorName: err.name,
        statusCode: err.statusCode,
        message: err.message,
      })
      return errorResponse(err.message, err.statusCode)
    }

    // Unhandled system errors: log full details server-side, return safe message to caller
    const errorMessage = err instanceof Error ? err.message : "Internal server error"
    logger.error("request.failed", { error: errorMessage })

    return errorResponse("Internal server error during reminder processing", 500)
  }
}
