"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

const ToggleGroupContext = React.createContext({
    value: undefined,
    onValueChange: () => { },
    type: "single",
})

const ToggleGroup = React.forwardRef(({ className, type = "single", value, onValueChange, children, ...props }, ref) => {
    return (
        <ToggleGroupContext.Provider value={{ value, onValueChange, type }}>
            <div
                ref={ref}
                className={cn("flex items-center justify-center gap-1", className)}
                {...props}
            >
                {children}
            </div>
        </ToggleGroupContext.Provider>
    )
})
ToggleGroup.displayName = "ToggleGroup"

const ToggleGroupItem = React.forwardRef(({ className, value, children, ...props }, ref) => {
    const context = React.useContext(ToggleGroupContext)
    const isSelected = context.type === "single"
        ? context.value === value
        : context.value?.includes(value)

    const handleClick = () => {
        if (context.type === "single") {
            context.onValueChange(value)
        } else {
            // Multi logic omitted for brevity as strictly not needed for this task, but safe to add if needed
        }
    }

    return (
        <button
            ref={ref}
            type="button"
            onClick={handleClick}
            data-state={isSelected ? "on" : "off"}
            className={cn(
                "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors hover:bg-muted hover:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 data-[state=on]:bg-accent data-[state=on]:text-accent-foreground",
                className
            )}
            {...props}
        >
            {children}
        </button>
    )
})
ToggleGroupItem.displayName = "ToggleGroupItem"

export { ToggleGroup, ToggleGroupItem }
