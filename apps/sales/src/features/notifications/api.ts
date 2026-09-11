import { client } from "@/core/api/client";
import type {
  PushSubscriptionCreate,
  PushSubscriptionResponse,
  TestNotificationRequest,
  VapidPublicKeyResponse,
} from "@/core/api/generated";

/**
 * Converts a URL-safe Base64 string to a Uint8Array for PushManager.
 */
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export function isPushNotificationSupported(): boolean {
  if (typeof window === "undefined") return false;
  return "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
}

export function getNotificationPermissionState(): NotificationPermission {
  if (typeof window === "undefined" || !("Notification" in window)) {
    return "denied";
  }
  return Notification.permission;
}

export async function getExistingPushSubscription(): Promise<PushSubscription | null> {
  if (!isPushNotificationSupported()) return null;

  try {
    const reg = await navigator.serviceWorker.ready;
    return await reg.pushManager.getSubscription();
  } catch {
    return null;
  }
}

export async function getVapidPublicKey(): Promise<string> {
  const res = await client.get<VapidPublicKeyResponse>("/v1/notifications/vapid-public-key");
  return res.public_key;
}

export async function subscribeToPushNotifications(): Promise<{
  success: boolean;
  error?: string;
}> {
  if (!isPushNotificationSupported()) {
    return {
      success: false,
      error: "Push notifications are not supported on this browser or device.",
    };
  }

  try {
    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      return {
        success: false,
        error: "Notification permission was not granted.",
      };
    }

    const publicKey = await getVapidPublicKey();
    if (!publicKey) {
      return {
        success: false,
        error: "Could not retrieve VAPID public key from server.",
      };
    }

    try {
      await navigator.serviceWorker.register("/sw.js", { scope: "/" });
    } catch (e) {
      console.warn("[Push] Service worker registration note:", e);
    }

    const registration = await navigator.serviceWorker.ready;
    if (!registration.active) {
      await new Promise<void>((resolve) => {
        const worker = registration.installing || registration.waiting;
        if (worker) {
          worker.addEventListener("statechange", () => {
            if (worker.state === "activated") resolve();
          });
          setTimeout(resolve, 500);
        } else {
          resolve();
        }
      });
    }

    const applicationServerKey = urlBase64ToUint8Array(publicKey);
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: applicationServerKey as BufferSource,
    });

    const subscriptionJson = subscription.toJSON();
    const p256dh = subscriptionJson.keys?.p256dh;
    const auth = subscriptionJson.keys?.auth;

    if (!p256dh || !auth) {
      return {
        success: false,
        error: "Invalid subscription keys returned by browser.",
      };
    }

    const payload: PushSubscriptionCreate = {
      endpoint: subscription.endpoint,
      keys: {
        p256dh,
        auth,
      },
      user_agent: typeof navigator !== "undefined" ? navigator.userAgent : undefined,
    };

    // Frozen API contract: POST /v1/notifications/subscribe
    await client.post<PushSubscriptionResponse>("/v1/notifications/subscribe", payload);

    return { success: true };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to enable notifications.";
    return { success: false, error: message };
  }
}

export async function unsubscribeFromPushNotifications(): Promise<{
  success: boolean;
  error?: string;
}> {
  if (!isPushNotificationSupported()) return { success: false };

  try {
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();

    if (subscription) {
      // Frozen API contract: DELETE /v1/notifications/unsubscribe?endpoint=...
      await client.delete<void>("/v1/notifications/unsubscribe", {
        params: { endpoint: subscription.endpoint },
      });
      await subscription.unsubscribe();
    }

    return { success: true };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to disable notifications.";
    return { success: false, error: message };
  }
}

export async function sendTestPushNotification(title?: string, message?: string) {
  const payload: TestNotificationRequest = {
    title: title || "FastUI Reminder Alert",
    body: message || "Your push notifications are successfully configured!",
    url: "/prospects",
  };

  // Frozen API contract: POST /v1/notifications/test
  return await client.post<{ message: string }>("/v1/notifications/test", payload);
}
