import * as React from "react"
import { LucideIcon } from "lucide-react"

export interface EmptyStateProps {
  icon?: LucideIcon
  title: string
  description: string
  primaryAction?: {
    label: string
    onClick: () => void
  }
  secondaryAction?: {
    label: string
    onClick: () => void
  }
  footerText?: string
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  primaryAction,
  secondaryAction,
  footerText
}: EmptyStateProps) {
  return (
    <div className="flex-1 flex flex-col items-center pt-[22vh] pb-8 px-4 bg-background h-full w-full relative">
      <div className="flex flex-col items-center w-full max-w-[420px] text-center">
        {Icon && (
          <div className="mb-[16px] flex justify-center text-muted-foreground/40">
            <Icon size={72} strokeWidth={1} />
          </div>
        )}

        <h1 className="text-[18px] leading-[26px] font-semibold text-foreground mb-2 transition-colors duration-300">
          {title}
        </h1>

        <p className="text-[16px] leading-[24px] font-normal text-muted-foreground mb-[24px] w-full transition-colors duration-300 max-w-[420px] text-center">
          {description}
        </p>

        {(primaryAction || secondaryAction) && (
          <div className="flex flex-col items-center w-full gap-[12px]">
            {primaryAction && (
              <button
                type="button"
                onClick={primaryAction.onClick}
                className="h-[44px] w-full max-w-[280px] rounded-full bg-primary text-primary-foreground hover:bg-primary/90 active:scale-[0.98] transition-all font-semibold text-[15px] cursor-pointer"
              >
                {primaryAction.label}
              </button>
            )}
            {secondaryAction && (
              <button
                type="button"
                onClick={secondaryAction.onClick}
                className="h-[44px] w-full max-w-[280px] rounded-full bg-secondary hover:bg-secondary/80 text-secondary-foreground active:scale-[0.98] transition-all font-medium text-[15px] cursor-pointer"
              >
                {secondaryAction.label}
              </button>
            )}
          </div>
        )}
      </div>

      {footerText && (
        <div className="absolute bottom-8 left-0 right-0 text-center">
          <p className="text-[13px] text-muted-foreground">
            {footerText}
          </p>
        </div>
      )}
    </div>
  )
}
