"use client"

import * as React from "react"
import { usePathname } from "next/navigation"
import { trackDemoEvent } from "@/lib/demo-api"

export function DemoAnalytics({ token }) {
  const pathname = usePathname()
  const reportedSessionRef = React.useRef(false)

  React.useEffect(() => {
    if (!token || typeof window === "undefined") return

    // Get or create session ID
    let sessionId = sessionStorage.getItem(`fastui_demo_sid_${token}`)
    if (!sessionId) {
      sessionId = `sess_${Math.random().toString(36).slice(2, 11)}_${Date.now()}`
      sessionStorage.setItem(`fastui_demo_sid_${token}`, sessionId)
    }

    // Only fire demo_viewed once per session mount
    if (!reportedSessionRef.current) {
      reportedSessionRef.current = true
      trackDemoEvent(token, {
        event_type: "demo_viewed",
        session_id: sessionId,
        page_path: pathname || window.location.pathname,
      })
    }
  }, [token, pathname])

  return null
}
