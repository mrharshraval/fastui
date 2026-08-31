import { api } from "@/lib/api"

/**
 * Converts a URL-safe Base64 string to a Uint8Array for PushManager.
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/")
  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

export function isPushNotificationSupported(): boolean {
  if (typeof window === "undefined") return false
  return (
    "serviceWorker" in navigator &&
    "PushManager" in window &&
    "Notification" in window
  )
}

export function getNotificationPermissionState(): NotificationPermission {
  if (typeof window === "undefined" || !("Notification" in window)) {
    return "denied"
  }
  return Notification.permission
}

export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!isPushNotificationSupported()) return null

  try {
    const registration = await navigator.serviceWorker.register("/sw.js", {
      scope: "/",
    })
    return registration
  } catch (error) {
    console.error("Failed to register Service Worker for notifications:", error)
    return null
  }
}

export async function getExistingPushSubscription(): Promise<PushSubscription | null> {
  if (!isPushNotificationSupported()) return null

  try {
    const reg = await navigator.serviceWorker.ready
    return await reg.pushManager.getSubscription()
  } catch {
    return null
  }
}

export async function subscribeToPushNotifications(): Promise<{
  success: boolean
  error?: string
}> {
  if (!isPushNotificationSupported()) {
    return {
      success: false,
      error: "Push notifications are not supported on this browser/device.",
    }
  }

  try {
    // 1. Request user permission
    const permission = await Notification.requestPermission()
    if (permission !== "granted") {
      return {
        success: false,
        error: "Notification permission was not granted.",
      }
    }

    // 2. Fetch VAPID public key
    const vapidRes = await api.get<{ public_key: string }>("/notifications/vapid-public-key")
    if (!vapidRes || !vapidRes.public_key) {
      return {
        success: false,
        error: "Could not retrieve VAPID public key from server.",
      }
    }

    // 3. Register service worker and wait for active state
    try {
      await navigator.serviceWorker.register("/sw.js", { scope: "/" })
    } catch (e) {
      console.warn("Service worker register call note:", e)
    }

    const registration = await navigator.serviceWorker.ready

    if (!registration.active) {
      await new Promise<void>((resolve) => {
        const worker = registration.installing || registration.waiting
        if (worker) {
          worker.addEventListener("statechange", () => {
            if (worker.state === "activated") resolve()
          })
          // Fallback timeout in case statechange fired already
          setTimeout(resolve, 500)
        } else {
          resolve()
        }
      })
    }

    const applicationServerKey = urlBase64ToUint8Array(vapidRes.public_key)
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: applicationServerKey as BufferSource,
    })


    const subscriptionJson = subscription.toJSON()
    const p256dh = subscriptionJson.keys?.p256dh
    const auth = subscriptionJson.keys?.auth

    if (!p256dh || !auth) {
      return {
        success: false,
        error: "Invalid subscription keys returned by browser.",
      }
    }

    // 4. Send subscription to API
    await api.post("/notifications/subscribe", {
      endpoint: subscription.endpoint,
      keys: {
        p256dh,
        auth,
      },
      user_agent: typeof navigator !== "undefined" ? navigator.userAgent : undefined,
    })

    return { success: true }
  } catch (error: any) {
    console.error("Failed to subscribe to push notifications:", error)
    return {
      success: false,
      error: error?.message || "Failed to enable notifications.",
    }
  }
}

export async function unsubscribeFromPushNotifications(): Promise<{
  success: boolean
  error?: string
}> {
  if (!isPushNotificationSupported()) return { success: false }

  try {
    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.getSubscription()

    if (subscription) {
      await api.delete(`/notifications/unsubscribe?endpoint=${encodeURIComponent(subscription.endpoint)}`)
      await subscription.unsubscribe()
    }

    return { success: true }
  } catch (error: any) {
    console.error("Failed to unsubscribe from push notifications:", error)
    return {
      success: false,
      error: error?.message || "Failed to disable notifications.",
    }
  }
}

export async function sendTestPushNotification(title?: string, body?: string) {
  return await api.post<{ status: string; dispatched_devices: number }>("/notifications/test", {
    title: title || "FastUI Reminder Alert",
    body: body || "Your phone push notifications are successfully configured!",
    url: "/prospects",
  })
}
