import * as React from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal } from "lucide-react";
import type { CompanyModel } from "../types";

interface CompaniesTabProps {
  companies: CompanyModel[];
  selectedCompanies: Set<string>;
  onToggleCompany: (id: string) => void;
  onToggleAll: () => void;
  isAllSelected: boolean;
  isSomeSelected: boolean;
  loading: boolean;
  onDeleteSingle: (id: string, name: string) => void;
}

export function CompaniesTab({
  companies,
  selectedCompanies,
  onToggleCompany,
  onToggleAll,
  isAllSelected,
  isSomeSelected,
  loading,
  onDeleteSingle,
}: CompaniesTabProps) {
  const isSelectionMode = selectedCompanies.size > 0;

  return (
    <>
      {/* Header Row */}
      <div className="flex items-center group/header w-full pb-2.5 select-none min-w-[700px]">
        <div className="w-9 shrink-0 flex items-center justify-center">
          <div
            className={`transition-opacity duration-150 ${
              isSelectionMode
                ? "opacity-100"
                : "opacity-0 group-hover/header:opacity-100 hover:opacity-100"
            }`}
          >
            <Checkbox
              checked={isAllSelected ? true : isSomeSelected ? "indeterminate" : false}
              onCheckedChange={onToggleAll}
              aria-label="Select all visible companies"
            />
          </div>
        </div>

        <div className="flex-1 grid grid-cols-12 gap-4 px-3 text-[14px] font-medium text-muted-foreground items-center">
          <div className="col-span-4">Company</div>
          <div className="col-span-3">Domain</div>
          <div className="col-span-3">Industry</div>
          <div className="col-span-2 text-right">Leads</div>
        </div>
      </div>

      {/* Rows */}
      <div className="flex flex-col w-full min-w-[700px]">
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center w-full py-2.5">
              <div className="w-9 shrink-0 flex items-center justify-center">
                <Skeleton className="size-4 rounded" />
              </div>
              <div className="flex-1 grid grid-cols-12 gap-4 px-3 items-center">
                <Skeleton className="col-span-4 h-4 rounded" />
                <Skeleton className="col-span-3 h-4 rounded" />
                <Skeleton className="col-span-3 h-4 rounded" />
                <Skeleton className="col-span-2 h-4 rounded" />
              </div>
            </div>
          ))
        ) : companies.length === 0 ? (
          <div className="py-16 text-center text-sm text-muted-foreground">
            No companies found.
          </div>
        ) : (
          companies.map((c, idx) => {
            const isSelected = selectedCompanies.has(c.id);
            const prevSelected = idx > 0 && selectedCompanies.has(companies[idx - 1].id);
            const nextSelected =
              idx < companies.length - 1 && selectedCompanies.has(companies[idx + 1].id);

            let selectionRounding = "rounded-xl";
            if (isSelected) {
              if (!prevSelected && nextSelected) {
                selectionRounding = "rounded-t-xl border-b border-border/40";
              } else if (prevSelected && nextSelected) {
                selectionRounding = "rounded-none border-b border-border/40";
              } else if (prevSelected && !nextSelected) {
                selectionRounding = "rounded-b-xl";
              } else {
                selectionRounding = "rounded-xl";
              }
            }

            return (
              <div key={c.id} className="flex items-center group/row w-full my-[1px] relative">
                <div className="w-9 shrink-0 flex items-center justify-center">
                  <div
                    className={`transition-opacity duration-150 ${
                      isSelected
                        ? "opacity-100"
                        : "opacity-0 group-hover/row:opacity-100 hover:opacity-100"
                    }`}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => onToggleCompany(c.id)}
                      aria-label={`Select ${c.name}`}
                    />
                  </div>
                </div>

                <div
                  onClick={() => onToggleCompany(c.id)}
                  className={`flex-1 grid grid-cols-12 gap-4 px-3 py-3 text-sm items-center transition-colors cursor-pointer ${
                    isSelected
                      ? `bg-secondary text-foreground ${selectionRounding}`
                      : "hover:bg-accent/50 rounded-xl"
                  }`}
                >
                  <div className="col-span-4 font-medium text-foreground truncate">
                    {c.name}
                  </div>
                  <div className="col-span-3 text-muted-foreground text-xs truncate">
                    {c.domain ?? "—"}
                  </div>
                  <div className="col-span-3 text-muted-foreground text-xs truncate">
                    {c.industry ?? "—"}
                  </div>
                  <div className="col-span-2 flex justify-end items-center gap-2">
                    <Badge variant="secondary" className="text-xs rounded-full px-2.5 py-0.5 font-normal">
                      {c.leads_count ?? 0} leads
                    </Badge>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                        <button
                          type="button"
                          aria-label="Company options"
                          className="size-7 rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent/80 transition-colors opacity-0 group-hover/row:opacity-100 cursor-pointer shrink-0"
                        >
                          <MoreHorizontal size={15} />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-36">
                        <DropdownMenuItem
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteSingle(c.id, c.name);
                          }}
                          className="text-destructive font-medium text-xs cursor-pointer"
                        >
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </>
  );
}
