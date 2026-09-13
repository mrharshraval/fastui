import * as React from "react";
import { X } from "lucide-react";
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
  searchSlot?: React.ReactNode;
}

export function ProspectsBulkBar({
  selectedCount,
  onClearSelection,
  onBulkApprove,
  onBulkQualify,
  onDeleteSelected,
  onExport,
  searchSlot,
}: ProspectsBulkBarProps) {
  return (
    <div className="flex items-center justify-between w-full h-9 animate-in fade-in duration-150">
      <div className="flex items-center gap-2 shrink-0">
        {/* Primary Approve Button */}
        <button
          type="button"
          onClick={onBulkApprove}
          className="flex items-center justify-center h-9 px-4 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 active:scale-95 text-sm font-medium transition-all cursor-pointer shrink-0"
        >
          <span>Approve</span>
        </button>

        {/* Qualify Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="h-9 px-3.5 rounded-full bg-secondary hover:bg-accent text-sm font-medium text-foreground transition-colors cursor-pointer shrink-0"
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
          className="h-9 px-3.5 rounded-full border border-destructive/30 text-destructive hover:bg-destructive-muted text-sm font-medium transition-colors cursor-pointer shrink-0"
        >
          Delete
        </button>

        {/* Export Button */}
        <button
          type="button"
          onClick={onExport}
          className="h-9 px-3.5 rounded-full bg-secondary hover:bg-accent text-sm font-medium text-foreground transition-colors cursor-pointer shrink-0"
        >
          Export
        </button>
      </div>

      <div className="flex items-center gap-3 shrink-0">
        <span className="text-sm text-muted-foreground font-normal shrink-0 whitespace-nowrap">
          {selectedCount} selected
        </span>
        <button
          type="button"
          onClick={onClearSelection}
          className="flex items-center justify-center size-7 rounded-full hover:bg-accent text-muted-foreground hover:text-foreground transition-colors cursor-pointer shrink-0"
          title="Clear selection"
        >
          <X size={18} />
        </button>
        {searchSlot}
      </div>
    </div>
  );
}
