import * as React from "react";
import { ListFilter, Check, CircleDashed, Activity, User, Calendar, Database } from "lucide-react";
import { cn } from "@/shared/lib/cn";
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

const renderSubMenu = (
  label: string,
  icon: React.ReactNode,
  options: { id: string; label: string }[],
  currentValue: string,
  onChange: (val: string) => void
) => (
  <DropdownMenuSub>
    <DropdownMenuSubTrigger className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500]">
      <div className="flex items-center gap-2">
        {icon}
        <span>{label}</span>
      </div>
    </DropdownMenuSubTrigger>
    <DropdownMenuPortal>
      <DropdownMenuSubContent className="w-48" sideOffset={8}>
        <div className="flex flex-col gap-1">
          {options.map((opt) => (
            <DropdownMenuItem
              key={opt.id}
              onClick={() => onChange(opt.id)}
              className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] transition-colors outline-none hover:bg-accent/60 text-foreground capitalize"
            >
              <span>{opt.label}</span>
              {currentValue === opt.id && <Check className="size-3.5" />}
            </DropdownMenuItem>
          ))}
        </div>
      </DropdownMenuSubContent>
    </DropdownMenuPortal>
  </DropdownMenuSub>
);

export interface LeadsFilterDropdownProps {
  filters: FilterState;
  onFilterChange: (key: keyof FilterState, value: string) => void;
  onResetFilters: () => void;
  className?: string;
}

export function LeadsFilterDropdown({
  filters,
  onFilterChange,
  onResetFilters,
  className,
}: LeadsFilterDropdownProps) {
  const activeFilterCount = Object.values(filters).filter((v) => v !== "all").length;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="Filter"
          className={cn(
            "relative flex items-center justify-center size-9 rounded-full bg-accent/50 hover:bg-accent/80 text-muted-foreground hover:text-foreground active:scale-95 transition-all cursor-pointer shrink-0",
            activeFilterCount > 0 && "text-foreground bg-accent",
            className
          )}
        >
          <ListFilter size={17} />
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
            <CircleDashed size={16} className="shrink-0 text-muted-foreground" />,
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
            <Activity size={16} className="shrink-0 text-muted-foreground" />,
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
            <User size={16} className="shrink-0 text-muted-foreground" />,
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
            <Calendar size={16} className="shrink-0 text-muted-foreground" />,
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
            <Database size={16} className="shrink-0 text-muted-foreground" />,
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
  );
}

export interface LeadsFilterBarProps {
  statusTab: string;
  onStatusTabChange: (tab: string) => void;
  filters: FilterState;
  onFilterChange: (key: keyof FilterState, value: string) => void;
  onResetFilters: () => void;
  hideDesktopFilter?: boolean;
}

export function LeadsFilterBar({
  statusTab,
  onStatusTabChange,
  filters,
  onFilterChange,
  onResetFilters,
  hideDesktopFilter = false,
}: LeadsFilterBarProps) {
  return (
    <div className={cn("flex items-center justify-between h-9", hideDesktopFilter ? "w-auto min-w-0 shrink-0" : "w-full")}>
      <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar min-w-0 shrink-0 h-9">
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

      <div className={cn("items-center", hideDesktopFilter ? "flex md:hidden" : "flex")}>
        <LeadsFilterDropdown
          filters={filters}
          onFilterChange={onFilterChange}
          onResetFilters={onResetFilters}
        />
      </div>
    </div>
  );
}
