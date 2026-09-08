"use client"

import * as React from "react"
import { DEFAULT_DENTAL_DEMO } from "./demo-api"

const DemoContext = React.createContext({
  token: "",
  demoData: DEFAULT_DENTAL_DEMO,
  business: DEFAULT_DENTAL_DEMO.business,
  customization: DEFAULT_DENTAL_DEMO.customization,
  isDemo: false,
  demoLink: (href) => href,
})

export function DemoProvider({ token, demoData, children }) {
  const effectiveData = demoData || DEFAULT_DENTAL_DEMO
  const business = effectiveData.business || DEFAULT_DENTAL_DEMO.business
  const customization = effectiveData.customization || DEFAULT_DENTAL_DEMO.customization
  const isDemo = Boolean(token)

  const demoLink = React.useCallback(
    (href) => {
      if (!token) return href
      if (!href || typeof href !== "string") return href
      if (href.startsWith("http://") || href.startsWith("https://") || href.startsWith("mailto:") || href.startsWith("tel:") || href.startsWith("#")) {
        return href
      }
      const cleanHref = href.startsWith("/") ? href : `/${href}`
      // Don't re-prefix if already prefixed
      if (cleanHref.startsWith(`/${token}`)) return cleanHref
      if (cleanHref === "/") return `/${token}`
      return `/${token}${cleanHref}`
    },
    [token]
  )

  const value = React.useMemo(
    () => ({
      token: token || "",
      demoData: effectiveData,
      business,
      customization,
      isDemo,
      demoLink,
    }),
    [token, effectiveData, business, customization, isDemo, demoLink]
  )

  return <DemoContext.Provider value={value}>{children}</DemoContext.Provider>
}

export function useDemo() {
  const ctx = React.useContext(DemoContext)
  return ctx
}
