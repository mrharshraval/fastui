// FastUI Service Worker for Phone Web Push Notifications

self.addEventListener("install", (event) => {
  self.skipWaiting()
})

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener("push", (event) => {
  if (!event.data) return

  let payload = {}
  try {
    payload = event.data.json()
  } catch (e) {
    payload = {
      title: "FastUI Reminder",
      body: event.data.text(),
    }
  }

  const title = payload.title || "FastUI Reminder"
  const options = {
    body: payload.body || "You have a sales follow-up reminder.",
    icon: payload.icon || "/assets/brand/icon/brand/primary/filled.png",
    badge: payload.badge || "/assets/brand/icon/brand/primary/filled.png",
    vibrate: [100, 50, 100],
    data: payload.data || { url: "/prospects" },
    tag: payload.tag || "fastui-reminder",
    renotify: true,
  }

  event.waitUntil(self.registration.showNotification(title, options))
})

self.addEventListener("notificationclick", (event) => {
  event.notification.close()

  const data = event.notification.data || {}
  const targetUrl = data.business_id
    ? `/business/${data.business_id}`
    : (data.url || "/prospects")

  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url && "focus" in client) {
          client.navigate(targetUrl)
          return client.focus()
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl)
      }
    })
  )
})
