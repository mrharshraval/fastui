import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Slot } from "radix-ui"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center gap-2 rounded-full border border-transparent bg-clip-padding font-[600] whitespace-nowrap outline-none select-none transition-colors ease-out cursor-pointer focus-visible:ring-4 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-5",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90 active:bg-primary/90",
        outline:
          "border-primary text-primary hover:bg-accent hover:text-accent-foreground font-[440]",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80 font-[440]",
        ghost:
          "hover:bg-accent hover:text-accent-foreground font-[440]",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90 font-[600]",
        link: "text-primary underline-offset-4 hover:underline font-[440]",
      },
      size: {
        default:
          "min-h-[40px] h-10 px-4 py-2 text-sm",
        sm: "min-h-[40px] h-10 rounded-full px-4 py-2 text-xs",
        lg: "min-h-[48px] h-12 rounded-full px-6 text-base",
        icon: "size-10 min-h-[40px]",
        "icon-sm": "size-8 min-h-[32px] p-0",
        "icon-xs": "size-6 min-h-[24px] p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot.Root : "button"

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }

