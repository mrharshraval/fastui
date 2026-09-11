import * as React from "react";
import { Download, X } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface LeadsBulkBarProps {
  selectedCount: number;
  onClearSelection: () => void;
  onBulkStatusChange: (status: string) => void;
  onBulkFollowUp: (time: string) => void;
  onBulkReminder: (time: string) => void;
  onDeleteSelected: () => void;
  onExport: () => void;
}

export function LeadsBulkBar({
  selectedCount,
  onClearSelection,
  onBulkStatusChange,
  onBulkFollowUp,
  onBulkReminder,
  onDeleteSelected,
  onExport,
}: LeadsBulkBarProps) {
  return (
    <div className="flex items-center justify-between w-full animate-in fade-in duration-150">
      <div className="flex items-center gap-2">
        {/* Change Status Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="h-9 px-3.5 rounded-full bg-secondary hover:bg-accent text-sm font-medium text-foreground transition-colors cursor-pointer"
            >
              Status
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-44">
            <div className="flex flex-col gap-1">
              {["new", "contacted", "qualified", "proposal", "won", "lost"].map((st) => (
                <DropdownMenuItem
                  key={st}
                  onClick={() => onBulkStatusChange(st)}
                  className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] capitalize transition-colors outline-none hover:bg-accent/60 text-foreground"
                >
                  {st}
                </DropdownMenuItem>
              ))}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Follow-up Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="h-9 px-3.5 rounded-full bg-secondary hover:bg-accent text-sm font-medium text-foreground transition-colors cursor-pointer"
            >
              Follow-up
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-44">
            <div className="flex flex-col gap-1">
              {[
                { id: "Tomorrow", label: "Tomorrow" },
                { id: "In 3 days", label: "In 3 days" },
                { id: "Next week", label: "Next week" },
                { id: "In 2 weeks", label: "In 2 weeks" },
              ].map((opt) => (
                <DropdownMenuItem
                  key={opt.id}
                  onClick={() => onBulkFollowUp(opt.id)}
                  className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] transition-colors outline-none hover:bg-accent/60 text-foreground"
                >
                  {opt.label}
                </DropdownMenuItem>
              ))}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Add Reminder Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="h-9 px-3.5 rounded-full bg-secondary hover:bg-accent text-sm font-medium text-foreground transition-colors cursor-pointer"
            >
              Reminder
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-44">
            <div className="flex flex-col gap-1">
              {[
                { id: "In 1 hour", label: "In 1 hour" },
                { id: "Today, 5 PM", label: "Today, 5 PM" },
                { id: "Tomorrow morning", label: "Tomorrow morning" },
                { id: "Next Monday", label: "Next Monday" },
              ].map((opt) => (
                <DropdownMenuItem
                  key={opt.id}
                  onClick={() => onBulkReminder(opt.id)}
                  className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] transition-colors outline-none hover:bg-accent/60 text-foreground"
                >
                  {opt.label}
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
