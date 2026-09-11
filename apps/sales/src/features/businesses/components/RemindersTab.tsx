import * as React from "react";
import { MoreHorizontal } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { ReminderItem } from "../types";

interface RemindersTabProps {
  reminders: ReminderItem[];
  onCompleteReminder: (rem: ReminderItem) => void;
  onDeleteReminder: (rem: ReminderItem) => void;
}

export function RemindersTab({
  reminders,
  onCompleteReminder,
  onDeleteReminder,
}: RemindersTabProps) {
  return (
    <div className="w-full max-w-[540px] mx-auto pb-8 animate-in fade-in duration-150">
      <div className="flex flex-col divide-y divide-border/20">
        {reminders.length === 0 ? (
          <p className="text-left text-xs text-muted-foreground py-2">
            No reminders scheduled.
          </p>
        ) : (
          reminders.map((rem) => (
            <div key={rem.id} className="flex flex-col py-3 first:pt-0 last:pb-0">
              <div className="flex items-center justify-between gap-3">
                <span className="text-[14px] font-medium text-foreground leading-snug">
                  {rem.title}
                </span>

                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs text-muted-foreground/80 font-normal tabular-nums">
                    {rem.due_date}
                  </span>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button
                        type="button"
                        className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer shrink-0"
                        aria-label="Reminder options"
                      >
                        <MoreHorizontal size={16} />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-36">
                      <DropdownMenuItem
                        onClick={() => onCompleteReminder(rem)}
                        className="min-h-8 px-2.5 rounded-xl cursor-pointer text-xs font-medium"
                      >
                        Complete
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => onDeleteReminder(rem)}
                        className="min-h-8 px-2.5 rounded-xl cursor-pointer text-xs font-medium text-destructive focus:text-destructive"
                      >
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>

              <span className="text-xs text-muted-foreground mt-0.5 font-normal">
                {rem.user_name || "You"}
              </span>

              {rem.notes && (
                <p className="text-[13px] text-muted-foreground/90 mt-1 leading-relaxed break-words">
                  {rem.notes}
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
