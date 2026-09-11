import * as React from "react";
import { ListFilter, Check, CircleDashed, Globe, Database, X } from "lucide-react";
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
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetDescription,
  SheetClose,
} from "@/components/ui/sheet";

export interface ProspectFilterState {
  qualification: string;
  website: string;
  source: string;
}

interface ProspectsFilterBarProps {
  statusTab: string;
  onStatusTabChange: (tab: string) => void;
  filters: ProspectFilterState;
  onFilterChange: (key: keyof ProspectFilterState, value: string) => void;
  onResetFilters: () => void;
}

export function ProspectsFilterBar({
  statusTab,
  onStatusTabChange,
  filters,
  onFilterChange,
  onResetFilters,
}: ProspectsFilterBarProps) {
  const [mobileFiltersOpen, setMobileFiltersOpen] = React.useState(false);
  const [pendingFilters, setPendingFilters] = React.useState({
    website: filters.website,
    source: filters.source,
  });

  const activeSecondaryFilterCount = [filters.website, filters.source].filter(
    (v) => v !== "all"
  ).length;

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

  return (
    <>
      <div className="flex items-center justify-between min-h-9 w-full">
        {/* Status Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 min-w-0 flex-1">
          {["all", "unqualified", "reviewing", "qualified", "disqualified"].map((tab) => (
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

        {/* Desktop Filter Dropdown */}
        <div className="hidden md:flex items-center">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                aria-label="Filter"
                className="relative flex items-center justify-center size-9 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-colors cursor-pointer shrink-0"
              >
                <ListFilter size={18} />
                {activeSecondaryFilterCount > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 size-4 rounded-full bg-primary text-primary-foreground text-[10px] flex items-center justify-center font-bold pointer-events-none">
                    {activeSecondaryFilterCount}
                  </span>
                )}
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <div className="flex items-center justify-between px-3 py-1.5 border-b border-border/40 mb-1">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Filter
                </span>
                {activeSecondaryFilterCount > 0 && (
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
                    { id: "unqualified", label: "Unqualified" },
                    { id: "reviewing", label: "Reviewing" },
                    { id: "qualified", label: "Qualified" },
                    { id: "disqualified", label: "Disqualified" },
                  ],
                  filters.qualification,
                  (v) => onFilterChange("qualification", v)
                )}

                {renderSubMenu(
                  "Website",
                  <Globe size={16} className="shrink-0 text-muted-foreground" />,
                  [
                    { id: "all", label: "Any" },
                    { id: "has_website", label: "Has Website" },
                    { id: "no_website", label: "No Website" },
                  ],
                  filters.website,
                  (v) => onFilterChange("website", v)
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
        </div>

        {/* Mobile Filter Button */}
        <div className="flex md:hidden items-center">
          <button
            type="button"
            aria-label="Filter"
            onClick={() => {
              setPendingFilters({
                website: filters.website,
                source: filters.source,
              });
              setMobileFiltersOpen(true);
            }}
            className="relative flex items-center justify-center size-9 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-colors cursor-pointer shrink-0"
          >
            <ListFilter size={18} />
            {activeSecondaryFilterCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 size-4 rounded-full bg-primary text-primary-foreground text-[10px] flex items-center justify-center font-bold pointer-events-none">
                {activeSecondaryFilterCount}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Mobile Filter Bottom Sheet */}
      <Sheet open={mobileFiltersOpen} onOpenChange={setMobileFiltersOpen}>
        <SheetContent
          side="bottom"
          className="max-h-[85vh] p-0 flex flex-col bg-background border-t border-border/50 rounded-t-[28px] outline-none"
          showCloseButton={false}
        >
          <div className="flex justify-center pt-3 pb-1 shrink-0">
            <div className="w-10 h-1 rounded-full bg-muted-foreground/30" />
          </div>

          <div className="flex items-center justify-between px-5 pt-2 pb-3 border-b border-border/30 shrink-0">
            <SheetTitle className="text-base font-semibold text-foreground">Filter</SheetTitle>
            <SheetClose asChild>
              <button
                type="button"
                aria-label="Close filter"
                className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer"
              >
                <X size={18} />
              </button>
            </SheetClose>
          </div>
          <SheetDescription className="sr-only">Filter prospects by website and source</SheetDescription>

          <div className="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-5">
            <div className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-1">
                Website
              </span>
              <div className="rounded-2xl border border-border/50 divide-y divide-border/30 overflow-hidden">
                {[
                  { id: "all", label: "Any" },
                  { id: "has_website", label: "Has Website" },
                  { id: "no_website", label: "No Website" },
                ].map((opt) => {
                  const isSelected = pendingFilters.website === opt.id;
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => setPendingFilters((prev) => ({ ...prev, website: opt.id }))}
                      className="w-full flex items-center justify-between min-h-[48px] px-4 text-left transition-colors hover:bg-accent/40 active:bg-accent/60 cursor-pointer"
                    >
                      <span
                        className={`text-[14px] ${
                          isSelected ? "font-semibold text-foreground" : "font-normal text-muted-foreground"
                        }`}
                      >
                        {opt.label}
                      </span>
                      {isSelected && <Check className="size-4 text-primary shrink-0 stroke-[2.5]" />}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-1">
                Source
              </span>
              <div className="rounded-2xl border border-border/50 divide-y divide-border/30 overflow-hidden">
                {[
                  { id: "all", label: "All Sources" },
                  { id: "discover", label: "Discover" },
                  { id: "import", label: "Import" },
                  { id: "manual", label: "Manual" },
                ].map((opt) => {
                  const isSelected = pendingFilters.source === opt.id;
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => setPendingFilters((prev) => ({ ...prev, source: opt.id }))}
                      className="w-full flex items-center justify-between min-h-[48px] px-4 text-left transition-colors hover:bg-accent/40 active:bg-accent/60 cursor-pointer"
                    >
                      <span
                        className={`text-[14px] ${
                          isSelected ? "font-semibold text-foreground" : "font-normal text-muted-foreground"
                        }`}
                      >
                        {opt.label}
                      </span>
                      {isSelected && <Check className="size-4 text-primary shrink-0 stroke-[2.5]" />}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="p-5 border-t border-border/30 flex items-center gap-3">
            <button
              type="button"
              onClick={() => {
                setPendingFilters({ website: "all", source: "all" });
                onResetFilters();
                setMobileFiltersOpen(false);
              }}
              className="flex-1 h-11 rounded-full border border-border/60 text-foreground font-medium text-sm hover:bg-accent transition-colors cursor-pointer"
            >
              Reset
            </button>
            <button
              type="button"
              onClick={() => {
                onFilterChange("website", pendingFilters.website);
                onFilterChange("source", pendingFilters.source);
                setMobileFiltersOpen(false);
              }}
              className="flex-1 h-11 rounded-full bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 transition-colors cursor-pointer"
            >
              Done
            </button>
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
