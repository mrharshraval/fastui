"use client"

import * as React from "react"
import { AlertDialog as AlertDialogPrimitive } from "radix-ui"
import { Download, Check, AlertCircle, Loader2, FileSpreadsheet } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  ExportType,
  ExportScope,
  ExportFilterParams,
  ExportStatusResponse,
  runExportAndDownload,
} from "@/lib/export"

export interface ExportDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  exportType: ExportType
  title?: string
  selectedCount?: number
  selectedIds?: number[]
  activeFilters?: ExportFilterParams
  filterSummary?: Array<{ label: string; value: string }>
}

export function ExportDialog({
  open,
  onOpenChange,
  exportType,
  title,
  selectedCount = 0,
  selectedIds = [],
  activeFilters = {},
  filterSummary = [],
}: ExportDialogProps) {
  const [scope, setScope] = React.useState<ExportScope>(
    selectedCount > 0 ? "selected" : "filtered"
  )
  const [isExporting, setIsExporting] = React.useState(false)
  const [progress, setProgress] = React.useState(0)
  const [statusText, setStatusText] = React.useState<string | null>(null)
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null)
  const [isSuccess, setIsSuccess] = React.useState(false)

  const abortControllerRef = React.useRef<AbortController | null>(null)

  // Reset state when dialog opens
  React.useEffect(() => {
    if (open) {
      setScope(selectedCount > 0 ? "selected" : "filtered")
      setIsExporting(false)
      setProgress(0)
      setStatusText(null)
      setErrorMessage(null)
      setIsSuccess(false)
    } else {
      // Abort ongoing export if modal is closed
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
        abortControllerRef.current = null
      }
    }
  }, [open, selectedCount])

  const handleStartExport = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault()
    if (isExporting) return

    setIsExporting(true)
    setProgress(5)
    setStatusText("Preparing export…")
    setErrorMessage(null)
    setIsSuccess(false)

    const controller = new AbortController()
    abortControllerRef.current = controller

    try {
      await runExportAndDownload({
        request: {
          export_type: exportType,
          scope,
          record_ids: scope === "selected" ? selectedIds : undefined,
          filters: activeFilters,
        },
        onProgress: (job: ExportStatusResponse) => {
          setProgress(Math.max(5, job.progress_percent))
          if (job.status === "processing") {
            if (job.total_records) {
              setStatusText(
                `Processed ${job.records_processed} of ${job.total_records} records…`
              )
            } else {
              setStatusText(`Processing records (${job.progress_percent}%)…`)
            }
          } else if (job.status === "completed") {
            setProgress(100)
            setStatusText("Download ready")
          }
        },
        signal: controller.signal,
      })

      setIsSuccess(true)
      setStatusText("Downloaded successfully")
      // Automatically close after a short friendly confirmation
      setTimeout(() => {
        onOpenChange(false)
      }, 1200)
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        // User aborted, silently reset
        setIsExporting(false)
        return
      }
      const msg = err instanceof Error ? err.message : "Export failed. Please try again."
      setErrorMessage(msg)
      setStatusText(null)
    } finally {
      setIsExporting(false)
      abortControllerRef.current = null
    }
  }

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    onOpenChange(false)
  }

  const typeLabel =
    exportType === "prospects"
      ? "Prospects"
      : exportType === "leads"
      ? "Leads"
      : "Records"

  const dialogTitle = title || `Export ${typeLabel}`

  return (
    <AlertDialogPrimitive.Root open={open} onOpenChange={isExporting ? () => {} : onOpenChange}>
      <AlertDialogPrimitive.Portal>
        {/* Subtle blurred backdrop */}
        <AlertDialogPrimitive.Overlay
          className="fixed inset-0 z-50 bg-black/75 backdrop-blur-[2px] duration-150 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=closed]:animate-out data-[state=closed]:fade-out-0"
        />

        {/* Modal Container */}
        <AlertDialogPrimitive.Content
          className={cn(
            "fixed top-1/2 left-1/2 z-50 -translate-x-1/2 -translate-y-1/2",
            "w-[calc(100%-2rem)] max-w-[440px]",
            "rounded-[22px] p-6 sm:p-7 shadow-2xl",
            "bg-card text-card-foreground dark:bg-[#212121] dark:text-white",
            "border border-border/50 dark:border-white/10 outline-none",
            "duration-150 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
            "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95"
          )}
        >
          {/* Header Title */}
          <div className="flex items-center justify-between">
            <AlertDialogPrimitive.Title className="text-xl font-bold tracking-tight text-foreground dark:text-white">
              {dialogTitle}
            </AlertDialogPrimitive.Title>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-accent/60 dark:bg-white/5 border border-border/40 dark:border-white/10 text-xs font-medium text-muted-foreground dark:text-neutral-300">
              <FileSpreadsheet size={13} className="text-primary" />
              <span>CSV</span>
            </div>
          </div>

          <AlertDialogPrimitive.Description asChild>
            <div className="mt-4 flex flex-col gap-4 text-sm leading-relaxed">
              {/* Scope Selection */}
              {selectedCount > 0 ? (
                <div className="flex flex-col gap-2">
                  <span className="text-xs font-semibold text-muted-foreground dark:text-neutral-400 uppercase tracking-wider">
                    Export Scope
                  </span>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      disabled={isExporting}
                      onClick={() => setScope("selected")}
                      className={cn(
                        "flex flex-col items-start p-3 rounded-xl border text-left transition-all cursor-pointer",
                        scope === "selected"
                          ? "border-primary bg-primary/10 text-foreground dark:text-white font-medium shadow-xs"
                          : "border-border/60 dark:border-white/10 hover:bg-accent/40 text-muted-foreground dark:text-neutral-300"
                      )}
                    >
                      <span className="text-sm font-semibold">Selected</span>
                      <span className="text-xs opacity-80 mt-0.5">
                        {selectedCount} {selectedCount === 1 ? "record" : "records"}
                      </span>
                    </button>

                    <button
                      type="button"
                      disabled={isExporting}
                      onClick={() => setScope("filtered")}
                      className={cn(
                        "flex flex-col items-start p-3 rounded-xl border text-left transition-all cursor-pointer",
                        scope === "filtered"
                          ? "border-primary bg-primary/10 text-foreground dark:text-white font-medium shadow-xs"
                          : "border-border/60 dark:border-white/10 hover:bg-accent/40 text-muted-foreground dark:text-neutral-300"
                      )}
                    >
                      <span className="text-sm font-semibold">All Matching</span>
                      <span className="text-xs opacity-80 mt-0.5">Full filtered set</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="rounded-xl p-3.5 bg-accent/40 dark:bg-white/5 border border-border/40 dark:border-white/5 flex flex-col gap-2">
                  <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground dark:text-neutral-400 uppercase tracking-wider">
                    <span>Exporting Dataset</span>
                    <span className="text-primary font-medium normal-case">Full filtered set</span>
                  </div>
                  {filterSummary.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {filterSummary.map((f, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs bg-background/80 dark:bg-[#1a1a1a] border border-border/50 text-foreground/80 dark:text-neutral-300"
                        >
                          <span className="text-muted-foreground">{f.label}:</span>
                          <span className="font-semibold text-foreground dark:text-white">{f.value}</span>
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground dark:text-neutral-400">
                      All available {typeLabel.toLowerCase()} will be exported.
                    </p>
                  )}
                </div>
              )}

              {/* Format & Injection Security Notice */}
              <div className="text-xs text-muted-foreground dark:text-neutral-400">
                Data will be exported in UTF-8 CSV format with spreadsheet formula sanitization for Excel and Google Sheets.
              </div>

              {/* Progress Bar & Status (While Exporting) */}
              {isExporting && (
                <div className="flex flex-col gap-2 p-3.5 rounded-xl bg-accent/50 dark:bg-white/5 border border-border/50 animate-in fade-in">
                  <div className="flex items-center justify-between text-xs font-medium text-foreground dark:text-white">
                    <span className="flex items-center gap-2">
                      <Loader2 size={13} className="animate-spin text-primary" />
                      {statusText || "Exporting…"}
                    </span>
                    <span>{progress}%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-background dark:bg-white/10 overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-300 rounded-full"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Success Notification */}
              {isSuccess && (
                <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium animate-in fade-in">
                  <Check size={15} className="shrink-0" />
                  <span>Download completed. The file has been saved to your downloads.</span>
                </div>
              )}

              {/* Error Message */}
              {errorMessage && (
                <div className="flex items-start gap-2 p-3 rounded-xl bg-destructive/10 border border-destructive/30 text-destructive text-xs leading-relaxed animate-in fade-in">
                  <AlertCircle size={15} className="shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-semibold">Export Failed</p>
                    <p className="mt-0.5 opacity-90">{errorMessage}</p>
                  </div>
                </div>
              )}
            </div>
          </AlertDialogPrimitive.Description>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2.5 mt-6 pt-1">
            <button
              type="button"
              disabled={isExporting && !abortControllerRef.current}
              onClick={handleCancel}
              className="inline-flex items-center justify-center h-10 px-5 rounded-full text-sm font-medium bg-secondary hover:bg-secondary/80 text-secondary-foreground dark:bg-[#2f2f2f] dark:hover:bg-[#383838] dark:text-white border border-border/40 dark:border-white/5 transition-all active:scale-95 cursor-pointer disabled:opacity-50 disabled:pointer-events-none"
            >
              {isSuccess ? "Done" : "Cancel"}
            </button>

            {!isSuccess && (
              <button
                type="button"
                disabled={isExporting}
                onClick={handleStartExport}
                className="inline-flex items-center gap-2 justify-center h-10 px-5 rounded-full text-sm font-semibold bg-primary hover:bg-primary/90 text-primary-foreground transition-all active:scale-95 cursor-pointer shadow-xs disabled:opacity-50 disabled:pointer-events-none"
              >
                {isExporting ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    <span>Exporting…</span>
                  </>
                ) : (
                  <>
                    <Download size={14} />
                    <span>Export</span>
                  </>
                )}
              </button>
            )}
          </div>
        </AlertDialogPrimitive.Content>
      </AlertDialogPrimitive.Portal>
    </AlertDialogPrimitive.Root>
  )
}
