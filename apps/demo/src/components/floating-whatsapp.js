"use client"

import * as React from "react"
import { useDemo } from "@/lib/demo-context"
import { trackDemoEvent } from "@/lib/demo-api"

export function FloatingWhatsApp() {
  const { business, customization, token } = useDemo()
  const rawWhatsapp = customization?.whatsapp_url || business?.whatsapp_url || business?.whatsapp || business?.phone

  if (!rawWhatsapp) return null

  const greeting = encodeURIComponent(
    `Hello ${business?.name || "there"}, I'm interested in booking a consultation.`
  )

  let waUrl = rawWhatsapp
  if (!rawWhatsapp.startsWith("http")) {
    const digits = rawWhatsapp.replace(/[^0-9]/g, "")
    if (!digits) return null
    const cleanPhone = digits.length === 10 ? `91${digits}` : digits
    waUrl = `https://wa.me/${cleanPhone}?text=${greeting}`
  } else if (!rawWhatsapp.includes("text=")) {
    waUrl = `${rawWhatsapp}${rawWhatsapp.includes("?") ? "&" : "?"}text=${greeting}`
  }

  const handleClick = () => {
    if (token) {
      trackDemoEvent(token, {
        event_type: "whatsapp_clicked",
        page_path: typeof window !== "undefined" ? window.location.pathname : "/",
      })
    }
  }

  return (
    <aside
      aria-label="Contact options"
      className="fixed bottom-6 right-6 z-40 animate-in fade-in slide-in-from-bottom-5 duration-500"
    >
      <a
        href={waUrl}
        target="_blank"
        rel="noopener noreferrer"
        onClick={handleClick}
        className="flex items-center justify-center h-14 w-14 rounded-full bg-[#25D366] text-white shadow-lg hover:shadow-xl hover:bg-[#20bd5a] hover:scale-105 active:scale-95 transition-all cursor-pointer"
        aria-label="WhatsApp"
      >
        <svg
          className="size-7 fill-current"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path d="M12.031 0C5.394 0 0 5.394 0 12.031c0 2.115.553 4.183 1.603 6.002L0 24l6.143-1.612A12.006 12.006 0 0012.031 24c6.637 0 12.031-5.394 12.031-12.031S18.668 0 12.031 0zm0 21.99c-1.83 0-3.626-.492-5.197-1.424l-.372-.222-3.864 1.013 1.031-3.766-.243-.387a9.986 9.986 0 01-1.535-5.173c0-5.526 4.496-10.022 10.022-10.022 5.526 0 10.022 4.496 10.022 10.022 0 5.526-4.496 10.022-10.022 10.022zm5.492-7.496c-.301-.151-1.782-.88-2.059-.98-.276-.1-.477-.151-.678.151-.201.301-.779.98-.955 1.181-.176.201-.352.226-.653.075-.301-.151-1.272-.469-2.423-1.496-.896-.799-1.501-1.787-1.677-2.088-.176-.301-.019-.464.132-.614.136-.135.301-.352.452-.527.151-.176.201-.301.301-.502.1-.201.05-.377-.025-.527-.075-.151-.678-1.633-.929-2.236-.245-.587-.494-.508-.678-.517-.176-.009-.377-.011-.578-.011s-.527.075-.804.377c-.276.301-1.055 1.03-1.055 2.512s1.08 2.914 1.231 3.115c.151.201 2.125 3.245 5.149 4.551.719.311 1.281.497 1.719.636.722.23 1.379.197 1.898.12.579-.086 1.782-.728 2.033-1.431.251-.703.251-1.306.176-1.431-.075-.126-.276-.201-.577-.352z" />
        </svg>
      </a>
    </aside>
  )
}
