"use client";

import * as React from "react";
import { AlertDialog as AlertDialogPrimitive } from "radix-ui";
import { Loader2 } from "lucide-react";
import { cn } from "@/shared/lib/cn";
import {
  type ExportType,
  type ExportFilterParams,
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
}: ExportDialogProps) {
  const scope = selectedCount > 0 ? "selected" : "filtered";
  const [isExporting, setIsExporting] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  const abortControllerRef = React.useRef<AbortController | null>(null);

  React.useEffect(() => {
    if (open) {
      setIsExporting(false);
      setErrorMessage(null);
    } else {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    }
  }, [open]);

  const handleStartExport = async (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (isExporting) return;

    setIsExporting(true);
    setErrorMessage(null);

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
        signal: controller.signal,
      });

      setIsExporting(false);
      onOpenChange(false);
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setIsExporting(false);
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

  const entityTitle =
    title ||
    (exportType === "prospects"
      ? "Prospects"
      : exportType === "leads"
      ? "Leads"
      : "Accounts");

  const displayText =
    selectedCount > 0
      ? `${selectedCount} ${
          exportType === "prospects"
            ? selectedCount === 1
              ? "prospect"
              : "prospects"
            : exportType === "leads"
            ? selectedCount === 1
              ? "lead"
              : "leads"
            : "items"
        } selected`
      : `All ${entityTitle.toLowerCase()} selected`;

  return (
    <AlertDialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <AlertDialogPrimitive.Portal>
        {/* Subtle blurred backdrop */}
        <AlertDialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/75 backdrop-blur-[2px] duration-150 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=closed]:animate-out data-[state=closed]:fade-out-0" />

        {/* Minimal Confirmation Container */}
        <AlertDialogPrimitive.Content
          className={cn(
            "fixed top-1/2 left-1/2 z-50 -translate-x-1/2 -translate-y-1/2",
            "w-[calc(100%-2rem)] max-w-[400px]",
            "rounded-[22px] p-6 shadow-2xl",
            "bg-card text-card-foreground dark:bg-[#212121] dark:text-white",
            "border border-border/50 dark:border-white/10 outline-none",
            "duration-150 data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
            "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95"
          )}
        >
          {/* Main confirmation line */}
          <AlertDialogPrimitive.Title className="text-base sm:text-lg font-semibold tracking-tight text-foreground dark:text-white">
            {displayText}
          </AlertDialogPrimitive.Title>

          <AlertDialogPrimitive.Description className="sr-only">
            Confirm export of selected items
          </AlertDialogPrimitive.Description>

          {errorMessage && (
            <p className="mt-2 text-xs text-destructive font-medium leading-relaxed">
              {errorMessage}
            </p>
          )}

          {/* Action Buttons: Cancel & Export */}
          <div className="flex items-center justify-end gap-2.5 mt-6 pt-1">
            <AlertDialogPrimitive.Cancel asChild>
              <button
                type="button"
                disabled={isExporting && !abortControllerRef.current}
                onClick={handleCancel}
                className="inline-flex items-center justify-center h-10 px-5 rounded-full text-sm font-medium bg-secondary hover:bg-secondary/80 text-secondary-foreground dark:bg-[#2f2f2f] dark:hover:bg-[#383838] dark:text-white border border-border/40 dark:border-white/5 transition-all active:scale-95 cursor-pointer disabled:opacity-50"
              >
                Cancel
              </button>
            </AlertDialogPrimitive.Cancel>

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
                <span>Export</span>
              )}
            </button>
          </div>
        </AlertDialogPrimitive.Content>
      </AlertDialogPrimitive.Portal>
    </AlertDialogPrimitive.Root>
  );
}
