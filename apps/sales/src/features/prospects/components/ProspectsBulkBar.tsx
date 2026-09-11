import * as React from "react";
import { Download, X } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface ProspectsBulkBarProps {
  selectedCount: number;
  onClearSelection: () => void;
  onBulkApprove: () => void;
  onBulkQualify: (status: string) => void;
  onDeleteSelected: () => void;
  onExport: () => void;
}

export function ProspectsBulkBar({
  selectedCount,
  onClearSelection,
  onBulkApprove,
  onBulkQualify,
  onDeleteSelected,
  onExport,
}: ProspectsBulkBarProps) {
  return (
    <div className="flex items-center justify-between w-full animate-in fade-in duration-150">
      <div className="flex items-center gap-2">
        {/* Primary Approve Button */}
        <button
          type="button"
          onClick={onBulkApprove}
          className="flex items-center justify-center h-9 px-4 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 active:scale-95 text-sm font-medium transition-all cursor-pointer"
        >
          <span>Approve</span>
        </button>

        {/* Qualify Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="h-9 px-3.5 rounded-full bg-secondary hover:bg-accent text-sm font-medium text-foreground transition-colors cursor-pointer"
            >
              Qualify
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-44">
            <div className="flex flex-col gap-1">
              {["unqualified", "reviewing", "qualified", "disqualified"].map((st) => (
                <DropdownMenuItem
                  key={st}
                  onClick={() => onBulkQualify(st)}
                  className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] capitalize transition-colors outline-none hover:bg-accent/60 text-foreground"
                >
                  {st}
                </DropdownMenuItem>
              ))}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Delete Button */}
        <button
          type="button"
          onClick={onDeleteSelected}
          className="h-9 px-3.5 rounded-full border border-destructive/30 text-destructive hover:bg-destructive-muted text-sm font-medium transition-colors cursor-pointer"
        >
          Delete
        </button>

        {/* Export Button */}
        <button
          type="button"
          onClick={onExport}
          className="flex items-center gap-1.5 h-9 px-3.5 rounded-full bg-secondary hover:bg-accent text-sm font-medium text-foreground transition-colors cursor-pointer"
        >
          <Download size={14} />
          <span>Export</span>
        </button>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground font-normal">
          {selectedCount} selected
        </span>
        <button
          type="button"
          onClick={onClearSelection}
          className="flex items-center justify-center size-7 rounded-full hover:bg-accent text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
          title="Clear selection"
        >
          <X size={20} />
        </button>
      </div>
    </div>
  );
}
