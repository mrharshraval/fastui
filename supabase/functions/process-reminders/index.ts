import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "@supabase/supabase-js"
import webpush from "web-push"

interface PushSubscriptionRecord {
  id: number
  user_id: number
  endpoint: string
  p256dh: string
  auth: string
  user_agent?: string
}

interface DueReminder {
  id: number
  business_id: number
  user_id: number | null
  title: string
  notes: string | null
  due_at: string
  business_name?: string
}

serve(async (req: Request) => {
  const startTime = Date.now()

  // 1. Verify HTTP method
  if (req.method !== "POST" && req.method !== "GET") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: { "Content-Type": "application/json" },
    })
  }

  // 2. Authorize Request (Supabase service role or CRON_SECRET)
  const authHeader = req.headers.get("Authorization")
  const cronSecret = Deno.env.get("CRON_SECRET")
  const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")

  let isAuthorized = false
  if (authHeader) {
    const token = authHeader.replace(/^Bearer\s+/i, "")
    if (serviceRoleKey && token === serviceRoleKey) {
      isAuthorized = true
    } else if (cronSecret && token === cronSecret) {
      isAuthorized = true
    }
  }

  if (!isAuthorized) {
    return new Response(JSON.stringify({ error: "Unauthorized access" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    })
  }

  // 3. Initialize Supabase Client
  const supabaseUrl = Deno.env.get("SUPABASE_URL")
  if (!supabaseUrl || !serviceRoleKey) {
    return new Response(
      JSON.stringify({ error: "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    )
  }

  const supabase = createClient(supabaseUrl, serviceRoleKey, {
    auth: { persistSession: false },
  })

  // 4. Configure VAPID
  const vapidPublicKey = Deno.env.get("VAPID_PUBLIC_KEY")
  const vapidPrivateKey = Deno.env.get("VAPID_PRIVATE_KEY")
  const vapidSubject = Deno.env.get("VAPID_SUBJECT") || "mailto:notifications@fastui.in"

  if (!vapidPublicKey || !vapidPrivateKey) {
    return new Response(
      JSON.stringify({ error: "Missing VAPID_PUBLIC_KEY or VAPID_PRIVATE_KEY in environment secrets" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    )
  }

  try {
    webpush.setVapidDetails(vapidSubject, vapidPublicKey, vapidPrivateKey)
  } catch (err: any) {
    console.error("Failed to initialize VAPID details:", err)
    return new Response(
      JSON.stringify({ error: "Invalid VAPID configuration", details: err?.message }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    )
  }

  // 5. Atomically Claim Due Reminders
  // Attempt to use stored procedure with FOR UPDATE SKIP LOCKED
  let dueReminders: DueReminder[] = []

  const { data: rpcData, error: rpcError } = await supabase.rpc("claim_due_reminders", {
    batch_limit: 50,
  })

  if (!rpcError && Array.isArray(rpcData)) {
    dueReminders = rpcData as DueReminder[]
  } else {
    // Fallback if claim_due_reminders stored procedure has not been executed yet
    console.warn("RPC claim_due_reminders not available or failed; running query fallback:", rpcError?.message)
    const now = new Date().toISOString()
    
    const { data: selectData, error: selectError } = await supabase
      .from("reminders")
      .select("id, business_id, user_id, title, notes, due_at")
      .eq("status", "pending")
      .lte("due_at", now)
      .is("notification_sent_at", null)
      .order("due_at", { ascending: true })
      .limit(50)

    if (selectError) {
      console.error("Failed to fetch due reminders:", selectError)
      return new Response(
        JSON.stringify({ error: "Database query failed", details: selectError.message }),
        { status: 500, headers: { "Content-Type": "application/json" } }
      )
    }

    if (selectData && selectData.length > 0) {
      const ids = selectData.map((r: any) => r.id)
      // Stamp notification_sent_at immediately for idempotency
      await supabase
        .from("reminders")
        .update({ notification_sent_at: now, updated_at: now })
        .in("id", ids)

      dueReminders = selectData as DueReminder[]
    }
  }

  if (dueReminders.length === 0) {
    return new Response(
      JSON.stringify({
        success: true,
        message: "No pending reminders due for notification",
        processed: 0,
        duration_ms: Date.now() - startTime,
      }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    )
  }

  console.log(`Processing ${dueReminders.length} due reminders for push delivery...`)

  // 6. Fetch Business Details if missing
  const missingBusinessIds = [
    ...new Set(
      dueReminders
        .filter((r) => !r.business_name && r.business_id)
        .map((r) => r.business_id)
    ),
  ]

  const businessMap = new Map<number, string>()
  if (missingBusinessIds.length > 0) {
    const { data: businesses } = await supabase
      .from("businesses")
      .select("id, business_name")
      .in("id", missingBusinessIds)

    if (businesses) {
      for (const b of businesses) {
        businessMap.set(b.id, b.business_name)
      }
    }
  }

  // 7. Batch Fetch Subscriptions for All Target Users (No N+1 Queries)
  const targetUserIds = [
    ...new Set(dueReminders.map((r) => r.user_id).filter((uid): uid is number => uid !== null)),
  ]

  const subscriptionsByUser = new Map<number, PushSubscriptionRecord[]>()
  if (targetUserIds.length > 0) {
    const { data: subscriptions, error: subError } = await supabase
      .from("push_subscriptions")
      .select("id, user_id, endpoint, p256dh, auth, user_agent")
      .in("user_id", targetUserIds)

    if (subError) {
      console.error("Failed to fetch push subscriptions:", subError)
    } else if (subscriptions) {
      for (const sub of subscriptions as PushSubscriptionRecord[]) {
        const existing = subscriptionsByUser.get(sub.user_id) || []
        existing.push(sub)
        subscriptionsByUser.set(sub.user_id, existing)
      }
    }
  }

  // 8. Dispatch Push Notifications with Failure Isolation
  let totalDispatched = 0
  const expiredEndpoints: string[] = []
  const deliveryPromises: Promise<void>[] = []

  for (const reminder of dueReminders) {
    const bizName =
      reminder.business_name ||
      businessMap.get(reminder.business_id) ||
      "FastUI Sales"

    const payload = JSON.stringify({
      title: `Reminder: ${bizName}`,
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

    const userSubs = reminder.user_id ? subscriptionsByUser.get(reminder.user_id) || [] : []

    if (userSubs.length === 0) {
      console.log(`Reminder #${reminder.id}: No push subscriptions registered for user #${reminder.user_id}`)
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
        })
        .catch((err: any) => {
          const statusCode = err?.statusCode || err?.status
          console.warn(`Push dispatch failed for endpoint ${sub.endpoint.slice(0, 45)}...: HTTP ${statusCode}`)
          // HTTP 404 (Not Found) or 410 (Gone) indicates the subscription has expired or been revoked
          if (statusCode === 404 || statusCode === 410) {
            expiredEndpoints.push(sub.endpoint)
          }
        })

      deliveryPromises.push(task)
    }
  }

  // Wait for all device dispatches to settle
  await Promise.allSettled(deliveryPromises)

  // 9. Prune Expired Subscriptions
  let prunedCount = 0
  if (expiredEndpoints.length > 0) {
    const uniqueExpired = [...new Set(expiredEndpoints)]
    console.log(`Purging ${uniqueExpired.length} expired/unsubscribed push endpoints...`)
    const { error: deleteError } = await supabase
      .from("push_subscriptions")
      .delete()
      .in("endpoint", uniqueExpired)

    if (deleteError) {
      console.error("Failed to purge expired subscriptions:", deleteError)
    } else {
      prunedCount = uniqueExpired.length
    }
  }

  const result = {
    success: true,
    reminders_claimed: dueReminders.length,
    notifications_sent: totalDispatched,
    devices_targeted: deliveryPromises.length,
    stale_subscriptions_cleaned: prunedCount,
    duration_ms: Date.now() - startTime,
  }

  console.log("Push notification processing summary:", JSON.stringify(result))

  return new Response(JSON.stringify(result), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  })
})
