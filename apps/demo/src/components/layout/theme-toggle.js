"use client"

import * as React from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"

export function ThemeToggle({ className }) {
    const [mounted, setMounted] = React.useState(false)
    const { setTheme, resolvedTheme } = useTheme()

    React.useEffect(() => {
        setMounted(true)
    }, [])

    if (!mounted) {
        return (
            <Button
                variant="ghost"
                size="icon"
                className={`h-9 w-9 rounded-full border border-border/40 bg-transparent text-muted-foreground ${className || ""}`}
                aria-label="Toggle theme"
            >
                <span className="h-4 w-4" />
            </Button>
        )
    }

    const isDark = resolvedTheme === "dark"

    return (
        <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(isDark ? "light" : "dark")}
            className={`h-9 w-9 rounded-full border border-border/40 hover:bg-muted text-foreground transition-colors ${className || ""}`}
            aria-label="Toggle theme"
        >
            {isDark ? (
                <Moon className="h-4 w-4 transition-all" />
            ) : (
                <Sun className="h-4 w-4 transition-all" />
            )}
            <span className="sr-only">Toggle theme</span>
        </Button>
    )
}
