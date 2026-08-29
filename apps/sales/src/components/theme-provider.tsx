"use client"

import * as React from "react"

type Theme = "dark" | "light" | "system"

interface ThemeContextType {
  theme: Theme
  resolvedTheme: "dark" | "light"
  setTheme: (theme: Theme) => void
  themes: Theme[]
}

const ThemeContext = React.createContext<ThemeContextType>({
  theme: "dark",
  resolvedTheme: "dark",
  setTheme: () => {},
  themes: ["dark", "light", "system"],
})

export function ThemeProvider({
  children,
  defaultTheme = "dark",
  storageKey = "theme",
}: {
  children: React.ReactNode
  defaultTheme?: Theme
  storageKey?: string
  attribute?: string
  disableTransitionOnChange?: boolean
  enableSystem?: boolean
}) {
  const [theme, setThemeState] = React.useState<Theme>(defaultTheme)
  const [resolvedTheme, setResolvedTheme] = React.useState<"dark" | "light">("dark")
  const [mounted, setMounted] = React.useState(false)

  const applyTheme = React.useCallback((t: Theme) => {
    const root = document.documentElement
    let resolved: "dark" | "light" = "dark"

    if (t === "system") {
      const systemDark = window.matchMedia("(prefers-color-scheme: dark)").matches
      resolved = systemDark ? "dark" : "light"
    } else {
      resolved = t
    }

    setResolvedTheme(resolved)
    root.classList.remove("light", "dark")
    root.classList.add(resolved)
    root.style.colorScheme = resolved
  }, [])

  // Initialize theme from storage on mount
  React.useEffect(() => {
    try {
      const saved = localStorage.getItem(storageKey) as Theme | null
      const initial = saved || defaultTheme
      setThemeState(initial)
      applyTheme(initial)
    } catch {
      applyTheme(defaultTheme)
    }
    setMounted(true)
  }, [defaultTheme, storageKey, applyTheme])

  // Listen for system theme changes if set to system
  React.useEffect(() => {
    if (!mounted || theme !== "system") return

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)")
    const handler = () => applyTheme("system")
    mediaQuery.addEventListener("change", handler)
    return () => mediaQuery.removeEventListener("change", handler)
  }, [mounted, theme, applyTheme])

  const setTheme = React.useCallback(
    (newTheme: Theme) => {
      setThemeState(newTheme)
      try {
        localStorage.setItem(storageKey, newTheme)
      } catch {}
      applyTheme(newTheme)
    },
    [storageKey, applyTheme]
  )

  const value = React.useMemo(
    () => ({
      theme,
      resolvedTheme,
      setTheme,
      themes: ["dark", "light", "system"] as Theme[],
    }),
    [theme, resolvedTheme, setTheme]
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  return React.useContext(ThemeContext)
}


