"use client"

import * as React from "react"
import { AlertDialog as AlertDialogPrimitive } from "radix-ui"
import { cn } from "@/lib/utils"

export interface DeleteConfirmationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  itemName?: string
  description?: React.ReactNode
  warningText?: string
  cancelText?: string
  confirmText?: string
  isDeleting?: boolean
  onConfirm: () => Promise<void> | void
}

export function DeleteConfirmationDialog({
  open,
  onOpenChange,
  title,
  itemName,
  description,
  warningText,
  cancelText = "Cancel",
  confirmText = "Delete",
  isDeleting = false,
  onConfirm,
}: DeleteConfirmationDialogProps) {
  const [internalDeleting, setInternalDeleting] = React.useState(false)
  const deleting = isDeleting || internalDeleting

  const handleConfirm = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault()
    if (deleting) return

    setInternalDeleting(true)
    try {
      await onConfirm()
      onOpenChange(false)
    } catch {
      // If error occurs, caller can handle or leave open
    } finally {
      setInternalDeleting(false)
    }
  }

  return (
    <AlertDialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <AlertDialogPrimitive.Portal>
        {/* Subtle blurred backdrop */}
        <AlertDialogPrimitive.Overlay
          className="fixed inset-0 z-50 bg-black/75 backdrop-blur-[2px] duration-150 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=closed]:animate-out data-[state=closed]:fade-out-0"
        />

        {/* Modal Container matching reference design */}
        <AlertDialogPrimitive.Content
          className={cn(
            "fixed top-1/2 left-1/2 z-50 -translate-x-1/2 -translate-y-1/2",
            "w-[calc(100%-2rem)] max-w-[420px]",
            "rounded-[22px] p-6 sm:p-7 shadow-2xl",
            "bg-card text-card-foreground dark:bg-[#212121] dark:text-white",
            "border border-border/50 dark:border-white/10 outline-none",
            "duration-150 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
            "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95"
          )}
        >
          {/* Header Title */}
          <AlertDialogPrimitive.Title className="text-xl font-bold tracking-tight text-foreground dark:text-white">
            {title}
          </AlertDialogPrimitive.Title>

          {/* Description / Explanation */}
          <AlertDialogPrimitive.Description asChild>
            <div className="mt-3 text-sm flex flex-col gap-1.5 leading-relaxed">
              {description ? (
                <div className="text-foreground/90 dark:text-neutral-200">
                  {description}
                </div>
              ) : itemName ? (
                <div className="text-foreground/90 dark:text-neutral-200">
                  This will delete{" "}
                  <strong className="font-semibold text-foreground dark:text-white">
                    {itemName}
                  </strong>
                  .
                </div>
              ) : null}

              {warningText && (
                <div className="text-muted-foreground dark:text-neutral-400">
                  {warningText}
                </div>
              )}
            </div>
          </AlertDialogPrimitive.Description>

          {/* Action Buttons: Secondary Cancel & Prominent Red Delete */}
          <div className="flex items-center justify-end gap-2.5 mt-6 pt-1">
            <AlertDialogPrimitive.Cancel asChild>
              <button
                type="button"
                disabled={deleting}
                className="inline-flex items-center justify-center h-10 px-5 rounded-full text-sm font-medium bg-secondary hover:bg-secondary/80 text-secondary-foreground dark:bg-[#2f2f2f] dark:hover:bg-[#383838] dark:text-white border border-border/40 dark:border-white/5 transition-all active:scale-95 cursor-pointer disabled:opacity-50 disabled:pointer-events-none"
              >
                {cancelText}
              </button>
            </AlertDialogPrimitive.Cancel>

            <button
              type="button"
              disabled={deleting}
              onClick={handleConfirm}
              className="inline-flex items-center justify-center h-10 px-5 rounded-full text-sm font-semibold bg-[#ff002a] hover:bg-[#e00025] text-white transition-all active:scale-95 cursor-pointer shadow-xs disabled:opacity-50 disabled:pointer-events-none"
            >
              {deleting ? "Deleting…" : confirmText}
            </button>
          </div>
        </AlertDialogPrimitive.Content>
      </AlertDialogPrimitive.Portal>
    </AlertDialogPrimitive.Root>
  )
}
