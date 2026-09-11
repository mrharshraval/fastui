import * as React from "react";
import { ListFilter, Check, CircleDashed, Activity, User, Calendar, Database } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
  DropdownMenuPortal,
} from "@/components/ui/dropdown-menu";

export interface FilterState {
  status: string;
  signal: string;
  owner: string;
  followUp: string;
  source: string;
}

interface LeadsFilterBarProps {
  statusTab: string;
  onStatusTabChange: (tab: string) => void;
  filters: FilterState;
  onFilterChange: (key: keyof FilterState, value: string) => void;
  onResetFilters: () => void;
}

export function LeadsFilterBar({
  statusTab,
  onStatusTabChange,
  filters,
  onFilterChange,
  onResetFilters,
}: LeadsFilterBarProps) {
  const activeFilterCount = Object.values(filters).filter((v) => v !== "all").length;

  const renderSubMenu = (
    label: string,
    icon: React.ReactNode,
    options: { id: string; label: string }[],
    currentValue: string,
    onChange: (val: string) => void
  ) => (
    <DropdownMenuSub>
      <DropdownMenuSubTrigger className="flex items-center gap-3 min-h-9 px-2.5 rounded-2xl cursor-pointer text-[14px] font-[500] hover:bg-accent/60 data-[state=open]:bg-accent/60">
        {icon}
        {label}
      </DropdownMenuSubTrigger>
      <DropdownMenuPortal>
        <DropdownMenuSubContent className="w-48" sideOffset={8}>
          <div className="flex flex-col gap-1">
            {options.map((opt) => (
              <DropdownMenuItem
                key={opt.id}
                onClick={() => onChange(opt.id)}
                className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[14px] font-[500] transition-colors outline-none border-none hover:bg-accent/60 text-foreground"
              >
                {opt.label}
                {currentValue === opt.id && <Check size={20} className="shrink-0" />}
              </DropdownMenuItem>
            ))}
          </div>
        </DropdownMenuSubContent>
      </DropdownMenuPortal>
    </DropdownMenuSub>
  );

  return (
    <div className="flex items-center justify-between min-h-9 w-full">
      <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 min-w-0 flex-1">
        {["all", "new", "active", "closed"].map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => onStatusTabChange(tab)}
            className={`h-9 px-3.5 rounded-full text-sm capitalize transition-colors cursor-pointer shrink-0 whitespace-nowrap ${
              statusTab === tab
                ? "bg-secondary text-foreground font-semibold md:bg-secondary md:text-foreground"
                : "text-muted-foreground hover:text-foreground font-medium"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="flex items-center">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              aria-label="Filter"
              className="relative flex items-center justify-center size-9 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-colors cursor-pointer shrink-0"
            >
              <ListFilter size={18} />
              {activeFilterCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 size-4 rounded-full bg-primary text-primary-foreground text-[10px] flex items-center justify-center font-bold pointer-events-none">
                  {activeFilterCount}
                </span>
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <div className="flex items-center justify-between px-3 py-1.5 border-b border-border/40 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Filter</span>
              {activeFilterCount > 0 && (
                <button
                  onClick={onResetFilters}
                  className="text-xs text-primary font-medium hover:underline cursor-pointer"
                >
                  Reset
                </button>
              )}
            </div>

            <div className="flex flex-col gap-1">
              {renderSubMenu(
                "Status",
                <CircleDashed size={20} className="shrink-0 text-muted-foreground" />,
                [
                  { id: "all", label: "All Statuses" },
                  { id: "new", label: "New" },
                  { id: "contacted", label: "Contacted" },
                  { id: "qualified", label: "Qualified" },
                  { id: "negotiating", label: "Negotiating" },
                  { id: "won", label: "Won" },
                  { id: "lost", label: "Lost" },
                ],
                filters.status,
                (v) => onFilterChange("status", v)
              )}

              {renderSubMenu(
                "Signal",
                <Activity size={20} className="shrink-0 text-muted-foreground" />,
                [
                  { id: "all", label: "All Signals" },
                  { id: "hot", label: "Hot" },
                  { id: "warm", label: "Warm" },
                  { id: "cold", label: "Cold" },
                ],
                filters.signal,
                (v) => onFilterChange("signal", v)
              )}

              {renderSubMenu(
                "Owner",
                <User size={20} className="shrink-0 text-muted-foreground" />,
                [
                  { id: "all", label: "Any Owner" },
                  { id: "unassigned", label: "Unassigned" },
                  { id: "me", label: "Assigned to me" },
                ],
                filters.owner,
                (v) => onFilterChange("owner", v)
              )}

              {renderSubMenu(
                "Follow-ups",
                <Calendar size={20} className="shrink-0 text-muted-foreground" />,
                [
                  { id: "all", label: "Any Time" },
                  { id: "overdue", label: "Overdue" },
                  { id: "today", label: "Due today" },
                  { id: "upcoming", label: "Upcoming" },
                  { id: "none", label: "None" },
                ],
                filters.followUp,
                (v) => onFilterChange("followUp", v)
              )}

              {renderSubMenu(
                "Source",
                <Database size={20} className="shrink-0 text-muted-foreground" />,
                [
                  { id: "all", label: "All Sources" },
                  { id: "discover", label: "Discover" },
                  { id: "import", label: "Import" },
                  { id: "manual", label: "Manual" },
                ],
                filters.source,
                (v) => onFilterChange("source", v)
              )}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
