"use client";

import * as React from "react";
import { AlertDialog as AlertDialogPrimitive } from "radix-ui";
import { Download, Check, AlertCircle, Loader2, FileSpreadsheet } from "lucide-react";
import { cn } from "@/shared/lib/cn";
import {
  type ExportType,
  type ExportScope,
  type ExportFilterParams,
  type ExportStatusResponse,
  runExportAndDownload,
} from "@/features/exports/api";

export interface ExportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  exportType: ExportType;
  title?: string;
  selectedCount?: number;
  selectedIds?: number[];
  activeFilters?: ExportFilterParams;
  filterSummary?: Array<{ label: string; value: string }>;
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
  );
  const [isExporting, setIsExporting] = React.useState(false);
  const [progress, setProgress] = React.useState(0);
  const [statusText, setStatusText] = React.useState<string | null>(null);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const [isSuccess, setIsSuccess] = React.useState(false);

  const abortControllerRef = React.useRef<AbortController | null>(null);

  React.useEffect(() => {
    if (open) {
      setScope(selectedCount > 0 ? "selected" : "filtered");
      setIsExporting(false);
      setProgress(0);
      setStatusText(null);
      setErrorMessage(null);
      setIsSuccess(false);
    } else {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    }
  }, [open, selectedCount]);

  const handleStartExport = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (isExporting) return;

    setIsExporting(true);
    setProgress(5);
    setStatusText("Preparing export…");
    setErrorMessage(null);
    setIsSuccess(false);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      await runExportAndDownload({
        request: {
          export_type: exportType,
          scope,
          record_ids: scope === "selected" ? selectedIds : undefined,
          filters: {
            search: activeFilters.search ?? null,
            qualification_status: activeFilters.qualification_status ?? null,
            stage: activeFilters.stage ?? null,
            signal: activeFilters.signal ?? null,
            priority: activeFilters.priority ?? null,
            website: activeFilters.website ?? null,
            source: activeFilters.source ?? null,
            sort_by: activeFilters.sort_by ?? null,
            sort_order: activeFilters.sort_order ?? null,
          },
        },
        onProgress: (job: ExportStatusResponse) => {
          setProgress(Math.max(5, job.progress_percent));
          if (job.status === "processing") {
            if (job.total_records) {
              setStatusText(
                `Processed ${job.records_processed} of ${job.total_records} records…`
              );
            } else {
              setStatusText(`Processing records (${job.progress_percent}%)…`);
            }
          } else if (job.status === "completed") {
            setProgress(100);
            setStatusText("Download ready");
          }
        },
        signal: controller.signal,
      });

      setIsSuccess(true);
      setIsExporting(false);
      setStatusText(null);
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setIsExporting(false);
        setStatusText(null);
        return;
      }
      setIsExporting(false);
      const msg = err instanceof Error ? err.message : "Export failed. Please try again.";
      setErrorMessage(msg);
    } finally {
      abortControllerRef.current = null;
    }
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    onOpenChange(false);
  };

  const entityTitle = title || (exportType === "prospects" ? "Prospects" : exportType === "leads" ? "Leads" : "Accounts");

  return (
    <AlertDialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <AlertDialogPrimitive.Portal>
        <AlertDialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200" />
        <AlertDialogPrimitive.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md p-6 bg-card border border-border/60 rounded-3xl shadow-2xl animate-in zoom-in-95 duration-200 focus:outline-none">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center justify-center w-10 h-10 rounded-2xl bg-primary/10 text-primary">
              <FileSpreadsheet size={20} />
            </div>
            <div>
              <AlertDialogPrimitive.Title className="text-lg font-semibold tracking-tight text-foreground">
                Export {entityTitle}
              </AlertDialogPrimitive.Title>
              <p className="text-xs text-muted-foreground">Download clean CSV data</p>
            </div>
          </div>

          <AlertDialogPrimitive.Description asChild>
            <div className="space-y-4 text-sm text-muted-foreground">
              {/* Scope Selection */}
              <div className="space-y-2">
                <label className="text-xs font-medium text-foreground">Records to include</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setScope("filtered")}
                    disabled={isExporting}
                    className={cn(
                      "flex flex-col items-start p-3 rounded-2xl border text-left transition-all cursor-pointer",
                      scope === "filtered"
                        ? "border-primary bg-primary/5 text-foreground ring-1 ring-primary"
                        : "border-border/50 hover:border-border text-muted-foreground"
                    )}
                  >
                    <span className="text-xs font-semibold">Matching filter</span>
                    <span className="text-[11px] opacity-75 mt-0.5">All matching current query</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setScope("selected")}
                    disabled={selectedCount === 0 || isExporting}
                    className={cn(
                      "flex flex-col items-start p-3 rounded-2xl border text-left transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed",
                      scope === "selected"
                        ? "border-primary bg-primary/5 text-foreground ring-1 ring-primary"
                        : "border-border/50 hover:border-border text-muted-foreground"
                    )}
                  >
                    <span className="text-xs font-semibold">Selected only</span>
                    <span className="text-[11px] opacity-75 mt-0.5">
                      {selectedCount > 0 ? `${selectedCount} selected` : "No items selected"}
                    </span>
                  </button>
                </div>
              </div>

              {/* Filter Summary */}
              {scope === "filtered" && filterSummary.length > 0 && (
                <div className="p-3 rounded-2xl bg-muted/50 border border-border/40 space-y-1.5">
                  <p className="text-[11px] font-medium text-foreground">Active filters applied:</p>
                  <div className="flex flex-wrap gap-1.5">
                    {filterSummary.map((f, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-background border border-border/40 text-foreground"
                      >
                        {f.label}: {f.value}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Progress Bar */}
              {isExporting && (
                <div className="space-y-2 p-3 rounded-2xl bg-muted/40 border border-border/40 animate-in fade-in">
                  <div className="flex items-center justify-between text-xs font-medium text-foreground">
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

              {/* Success */}
              {isSuccess && (
                <div className="flex items-center gap-2 p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium animate-in fade-in">
                  <Check size={15} className="shrink-0" />
                  <span>Download completed and saved to your device.</span>
                </div>
              )}

              {/* Error */}
              {errorMessage && (
                <div className="flex items-start gap-2 p-3 rounded-2xl bg-destructive/10 border border-destructive/30 text-destructive text-xs leading-relaxed animate-in fade-in">
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
              className="inline-flex items-center justify-center h-10 px-5 rounded-full text-sm font-medium bg-secondary hover:bg-secondary/80 text-secondary-foreground border border-border/40 transition-all active:scale-95 cursor-pointer disabled:opacity-50"
            >
              {isSuccess ? "Done" : "Cancel"}
            </button>

            {!isSuccess && (
              <button
                type="button"
                disabled={isExporting}
                onClick={handleStartExport}
                className="inline-flex items-center gap-2 justify-center h-10 px-5 rounded-full text-sm font-semibold bg-primary hover:bg-primary/90 text-primary-foreground transition-all active:scale-95 cursor-pointer shadow-xs disabled:opacity-50"
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
  );
}
