"use client";

import * as React from "react";
import { Columns3, Check } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

export interface ColumnConfig {
  key: string;
  label: string;
  gridTrack: string;
  canHide?: boolean;
}

export interface ColumnVisibilityDropdownProps {
  columns: ColumnConfig[];
  visibleColumns: Record<string, boolean>;
  onToggleColumn: (key: string) => void;
  onReset: () => void;
  className?: string;
}

export function ColumnVisibilityDropdown({
  columns,
  visibleColumns,
  onToggleColumn,
  onReset,
  className,
}: ColumnVisibilityDropdownProps) {
  const hiddenCount = columns.filter(
    (col) => col.canHide !== false && visibleColumns[col.key] === false
  ).length;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="Columns"
          title="Columns"
          className={cn(
            "relative flex items-center justify-center size-9 rounded-full bg-accent/50 hover:bg-accent/80 text-muted-foreground hover:text-foreground active:scale-95 transition-all cursor-pointer shrink-0",
            hiddenCount > 0 && "text-foreground bg-accent",
            className
          )}
        >
          <Columns3 size={17} />
          {hiddenCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 size-4 rounded-full bg-primary text-primary-foreground text-[10px] flex items-center justify-center font-bold pointer-events-none">
              {hiddenCount}
            </span>
          )}
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-52">
        <div className="flex items-center justify-between px-3 py-1.5 border-b border-border/40 mb-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Columns
          </span>
          {hiddenCount > 0 && (
            <button
              type="button"
              onClick={onReset}
              className="text-xs text-primary font-medium hover:underline cursor-pointer"
            >
              Show All
            </button>
          )}
        </div>

        <div className="flex flex-col gap-0.5">
          {columns.map((col) => {
            const isVisible = visibleColumns[col.key] !== false;
            const isLocked = col.canHide === false;

            return (
              <DropdownMenuItem
                key={col.key}
                disabled={isLocked}
                onSelect={(e) => {
                  e.preventDefault();
                  if (!isLocked) {
                    onToggleColumn(col.key);
                  }
                }}
                className={cn(
                  "flex items-center justify-between min-h-9 px-2.5 rounded-xl text-[13px] font-[500] transition-colors outline-none",
                  isLocked
                    ? "opacity-50 cursor-not-allowed text-muted-foreground"
                    : "cursor-pointer hover:bg-accent/60 text-foreground"
                )}
              >
                <div className="flex items-center gap-2">
                  <span>{col.label}</span>
                  {isLocked && (
                    <span className="text-[10px] text-muted-foreground font-normal">
                      (Required)
                    </span>
                  )}
                </div>
                {isVisible && <Check className="size-3.5 text-primary shrink-0" />}
              </DropdownMenuItem>
            );
          })}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function useColumnVisibility(storageKey: string) {
  const [visibleColumns, setVisibleColumns] = React.useState<Record<string, boolean>>({});

  React.useEffect(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        setVisibleColumns(JSON.parse(saved));
      }
    } catch {
      // ignore
    }
  }, [storageKey]);

  const toggleColumn = React.useCallback(
    (key: string) => {
      setVisibleColumns((prev) => {
        const next = { ...prev, [key]: prev[key] === false ? true : false };
        try {
          localStorage.setItem(storageKey, JSON.stringify(next));
        } catch {}
        return next;
      });
    },
    [storageKey]
  );

  const resetColumns = React.useCallback(() => {
    setVisibleColumns({});
    try {
      localStorage.removeItem(storageKey);
    } catch {}
  }, [storageKey]);

  return {
    visibleColumns,
    toggleColumn,
    resetColumns,
  };
}
