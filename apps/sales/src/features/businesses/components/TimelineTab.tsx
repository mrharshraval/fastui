import * as React from "react";
import { MoreHorizontal } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { ActivityItem } from "../types";

interface TimelineTabProps {
  activities: ActivityItem[];
  onDeleteActivity: (act: ActivityItem) => void;
}

function ActivityItemRow({
  act,
  onDelete,
}: {
  act: ActivityItem;
  onDelete: () => void;
}) {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const notes = act.notes?.trim();
  const MAX_CHARS = 8;
  const isLong = Boolean(notes && notes.length > MAX_CHARS);

  return (
    <div className="flex flex-col py-1.5 first:pt-0 last:pb-0">
      <div className="flex items-start justify-between gap-3 w-full">
        <span className="text-[13.5px] font-[500] text-foreground leading-snug min-w-0 flex-1 break-words">
          {act.action}
        </span>

        <div className="flex items-center gap-2 shrink-0 ml-auto pt-0.5">
          <span className="text-xs text-muted-foreground tabular-nums font-normal select-none">
            {act.timestamp}
          </span>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                className="flex items-center justify-center size-6 rounded-md text-muted-foreground/70 hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer shrink-0 -mr-1"
                aria-label="Activity options"
              >
                <MoreHorizontal size={14} />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-32">
              <DropdownMenuItem
                onClick={onDelete}
                className="min-h-8 px-2.5 rounded-xl cursor-pointer text-xs font-medium text-destructive focus:text-destructive"
              >
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {notes && (
        <div className="text-xs text-muted-foreground/90 mt-0.5 leading-relaxed break-words">
          {isLong && !isExpanded ? (
            <span>
              {notes.slice(0, MAX_CHARS).trim()}{" "}
              <span className="text-muted-foreground/50 select-none">·</span>{" "}
              <button
                type="button"
                onClick={() => setIsExpanded(true)}
                className="inline text-foreground font-medium hover:underline text-xs cursor-pointer"
              >
                Read more
              </button>
            </span>
          ) : isLong && isExpanded ? (
            <span>
              {notes}{" "}
              <span className="text-muted-foreground/50 select-none">·</span>{" "}
              <button
                type="button"
                onClick={() => setIsExpanded(false)}
                className="inline text-muted-foreground hover:text-foreground font-medium hover:underline text-xs cursor-pointer"
              >
                Show less
              </button>
            </span>
          ) : (
            <span>{notes}</span>
          )}
        </div>
      )}

      <div className="text-xs text-muted-foreground font-normal mt-0.5">
        {act.user_name || "You"}
      </div>
    </div>
  );
}

export function TimelineTab({ activities, onDeleteActivity }: TimelineTabProps) {
  return (
    <div className="w-full max-w-[540px] mx-auto pb-8 animate-in fade-in duration-150">
      {activities.length === 0 ? (
        <p className="text-left text-xs text-muted-foreground py-2">
          No activity recorded yet.
        </p>
      ) : (
        <div className="flex flex-col space-y-4">
          {activities.map((act) => (
            <ActivityItemRow
              key={act.id}
              act={act}
              onDelete={() => onDeleteActivity(act)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
