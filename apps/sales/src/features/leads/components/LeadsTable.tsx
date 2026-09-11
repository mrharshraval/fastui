import * as React from "react";
import Link from "next/link";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
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
import { MoreHorizontal, Check } from "lucide-react";
import { formatDate } from "@/lib/utils";
import type { LeadModel } from "../types";

interface LeadsTableProps {
  leads: LeadModel[];
  selectedLeads: Set<string>;
  onToggleLead: (id: string) => void;
  onToggleAll: () => void;
  isAllSelected: boolean;
  isSomeSelected: boolean;
  loading: boolean;
  loadingMore: boolean;
  hasMore: boolean;
  loadMoreError: string | null;
  onLoadMore: () => void;
  onStatusChange: (id: string, status: string) => void;
  onDeleteSingle: (id: string, name: string) => void;
  onAction: (lead: LeadModel, type: "website" | "call" | "email" | "whatsapp", value: string) => void;
  sentinelRef: React.RefObject<HTMLDivElement | null>;
}

export function LeadsTable({
  leads,
  selectedLeads,
  onToggleLead,
  onToggleAll,
  isAllSelected,
  isSomeSelected,
  loading,
  loadingMore,
  loadMoreError,
  onLoadMore,
  onStatusChange,
  onDeleteSingle,
  onAction,
  sentinelRef,
}: LeadsTableProps) {
  const isSelectionMode = selectedLeads.size > 0;

  return (
    <div className="flex flex-col -ml-12 w-[calc(100%+3rem)] overflow-x-auto">
      {/* Table Header Row */}
      <div className="flex items-center group/header w-full pb-2.5 select-none min-w-[900px]">
        {/* Checkbox Gutter Column */}
        <div className="w-9 shrink-0 flex items-center justify-center">
          <div
            className={`transition-opacity duration-150 ${
              isSelectionMode ? "opacity-100" : "opacity-0 group-hover/header:opacity-100 hover:opacity-100"
            }`}
          >
            <Checkbox
              checked={isAllSelected ? true : isSomeSelected ? "indeterminate" : false}
              onCheckedChange={onToggleAll}
              aria-label="Select all visible leads"
            />
          </div>
        </div>

        {/* Column Titles */}
        <div className="flex-1 grid grid-cols-[minmax(180px,2fr)_minmax(140px,1.4fr)_minmax(140px,1.3fr)_minmax(140px,1.3fr)_minmax(170px,1.5fr)_minmax(90px,0.9fr)_minmax(80px,0.8fr)_36px] gap-4 px-3 text-[14px] font-medium text-muted-foreground items-center">
          <div>Business</div>
          <div>Location</div>
          <div>Website</div>
          <div>Phone</div>
          <div>Email</div>
          <div>WhatsApp</div>
          <div className="text-right">Added</div>
          <div className="w-8" />
        </div>
      </div>

      {/* Table Body Rows */}
      <div className="flex flex-col w-full min-w-[900px]">
        {loading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-center w-full py-2.5">
              <div className="w-9 shrink-0 flex items-center justify-center">
                <Skeleton className="size-4 rounded" />
              </div>
              <div className="flex-1 grid grid-cols-[minmax(180px,2fr)_minmax(140px,1.4fr)_minmax(140px,1.3fr)_minmax(140px,1.3fr)_minmax(170px,1.5fr)_minmax(90px,0.9fr)_minmax(80px,0.8fr)_36px] gap-4 px-3 items-center">
                <Skeleton className="h-4 rounded" />
                <Skeleton className="h-4 rounded" />
                <Skeleton className="h-4 rounded" />
                <Skeleton className="h-4 rounded" />
                <Skeleton className="h-4 rounded" />
                <Skeleton className="h-4 rounded" />
                <Skeleton className="h-4 rounded" />
                <Skeleton className="size-5 rounded-full justify-self-end" />
              </div>
            </div>
          ))
        ) : leads.length === 0 ? (
          <div className="py-16 text-center text-sm text-muted-foreground">
            No leads found.
          </div>
        ) : (
          leads.map((lead, idx) => {
            const isSelected = selectedLeads.has(lead.id);
            const prevSelected = idx > 0 && selectedLeads.has(leads[idx - 1].id);
            const nextSelected = idx < leads.length - 1 && selectedLeads.has(leads[idx + 1].id);

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
              <div key={lead.id} className="flex items-center group/row w-full my-[1px] relative">
                {/* Checkbox Column */}
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
                      onCheckedChange={() => onToggleLead(lead.id)}
                      aria-label={`Select ${lead.business_name}`}
                    />
                  </div>
                </div>

                {/* Main Row Content */}
                <div
                  onClick={() => onToggleLead(lead.id)}
                  className={`flex-1 grid grid-cols-[minmax(180px,2fr)_minmax(140px,1.4fr)_minmax(140px,1.3fr)_minmax(140px,1.3fr)_minmax(170px,1.5fr)_minmax(90px,0.9fr)_minmax(80px,0.8fr)_36px] gap-4 px-3 py-3 text-sm items-center transition-colors cursor-pointer ${
                    isSelected
                      ? `bg-secondary text-foreground ${selectionRounding}`
                      : "hover:bg-accent/50 rounded-xl"
                  }`}
                >
                  {/* 1. Business */}
                  <div className="flex items-center min-w-0">
                    <Link
                      href={`/business/${lead.id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="font-medium text-foreground hover:text-primary transition-colors truncate"
                      title={lead.business_name}
                    >
                      {lead.business_name}
                    </Link>
                  </div>

                  {/* 2. Location */}
                  <div className="text-muted-foreground text-xs truncate" title={lead.location || "—"}>
                    {lead.location || "—"}
                  </div>

                  {/* 3. Website */}
                  <div className="min-w-0">
                    {lead.website ? (
                      <a
                        href={lead.website.startsWith("http") ? lead.website : `https://${lead.website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => {
                          e.stopPropagation();
                          onAction(lead, "website", lead.website!);
                        }}
                        className="inline-flex items-center text-xs text-muted-foreground hover:text-foreground hover:underline truncate transition-colors max-w-full group/link py-1 px-1.5 -ml-1.5 rounded-lg hover:bg-accent/50"
                        title={`Open ${lead.website}`}
                      >
                        <span className="truncate">
                          {lead.website.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "")}
                        </span>
                      </a>
                    ) : (
                      <span className="text-xs text-muted-foreground/40">—</span>
                    )}
                  </div>

                  {/* 4. Phone */}
                  <div className="min-w-0">
                    {lead.phone ? (
                      <a
                        href={`tel:${lead.phone}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          onAction(lead, "call", lead.phone!);
                        }}
                        className="inline-flex items-center text-xs text-muted-foreground hover:text-foreground hover:underline truncate transition-colors max-w-full group/phone py-1 px-1.5 -ml-1.5 rounded-lg hover:bg-accent/50"
                        title={`Call ${lead.phone}`}
                      >
                        <span className="truncate">{lead.phone}</span>
                      </a>
                    ) : (
                      <span className="text-xs text-muted-foreground/40">—</span>
                    )}
                  </div>

                  {/* 5. Email */}
                  <div className="min-w-0">
                    {lead.email ? (
                      <a
                        href={`mailto:${lead.email}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          onAction(lead, "email", lead.email!);
                        }}
                        className="inline-flex items-center text-xs text-muted-foreground hover:text-foreground hover:underline truncate transition-colors max-w-full group/email py-1 px-1.5 -ml-1.5 rounded-lg hover:bg-accent/50"
                        title={`Email ${lead.email}`}
                      >
                        <span className="truncate">{lead.email}</span>
                      </a>
                    ) : (
                      <span className="text-xs text-muted-foreground/40">—</span>
                    )}
                  </div>

                  {/* 6. WhatsApp */}
                  <div className="min-w-0">
                    {lead.whatsapp || lead.phone ? (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          const targetNumber = (lead.whatsapp || lead.phone || "").replace(/[^0-9]/g, "");
                          window.open(`https://wa.me/${targetNumber}`, "_blank", "noopener,noreferrer");
                          onAction(lead, "whatsapp", lead.whatsapp || lead.phone!);
                        }}
                        className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-success-muted text-success hover:bg-success/20 active:scale-95 transition-all cursor-pointer"
                        title={`Chat on WhatsApp (${lead.whatsapp || lead.phone})`}
                      >
                        <span>Chat</span>
                      </button>
                    ) : (
                      <span className="text-xs text-muted-foreground/40">—</span>
                    )}
                  </div>

                  {/* 7. Added */}
                  <div className="text-xs text-muted-foreground text-right truncate">
                    {formatDate(lead.created_at)}
                  </div>

                  {/* 8. Actions Menu */}
                  <div className="flex justify-end" onClick={(e) => e.stopPropagation()}>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <button
                          type="button"
                          aria-label="Lead options"
                          className="flex items-center justify-center size-7 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/80 active:scale-95 transition-all cursor-pointer opacity-0 group-hover/row:opacity-100 focus:opacity-100"
                        >
                          <MoreHorizontal size={15} />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-44">
                        <DropdownMenuSub>
                          <DropdownMenuSubTrigger className="flex items-center min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500]">
                            Change Status
                          </DropdownMenuSubTrigger>
                          <DropdownMenuPortal>
                            <DropdownMenuSubContent className="w-40">
                              {["new", "contacted", "qualified", "proposal", "won", "lost"].map((st) => (
                                <DropdownMenuItem
                                  key={st}
                                  onClick={() => onStatusChange(lead.id, st)}
                                  className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] capitalize"
                                >
                                  <span>{st}</span>
                                  {lead.status === st && <Check className="size-3.5" />}
                                </DropdownMenuItem>
                              ))}
                            </DropdownMenuSubContent>
                          </DropdownMenuPortal>
                        </DropdownMenuSub>

                        <DropdownMenuItem
                          onClick={() => onDeleteSingle(lead.id, lead.business_name)}
                          className="flex items-center min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] text-destructive hover:bg-destructive-muted"
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

        {/* Infinite Scroll Sentinel */}
        <div ref={sentinelRef} className="w-full">
          {loadingMore && (
            <div className="flex flex-col w-full py-1">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center w-full py-2.5">
                  <div className="w-9 shrink-0 flex items-center justify-center">
                    <Skeleton className="size-4 rounded" />
                  </div>
                  <div className="flex-1 grid grid-cols-[minmax(180px,2fr)_minmax(140px,1.4fr)_minmax(140px,1.3fr)_minmax(140px,1.3fr)_minmax(170px,1.5fr)_minmax(90px,0.9fr)_minmax(80px,0.8fr)_36px] gap-4 px-3 items-center">
                    <Skeleton className="h-4 rounded" />
                    <Skeleton className="h-4 rounded" />
                    <Skeleton className="h-4 rounded" />
                    <Skeleton className="h-4 rounded" />
                    <Skeleton className="h-4 rounded" />
                    <Skeleton className="h-4 rounded" />
                    <Skeleton className="h-4 rounded" />
                    <div />
                  </div>
                </div>
              ))}
            </div>
          )}
          {loadMoreError && (
            <div className="py-4 text-center">
              <button
                type="button"
                onClick={onLoadMore}
                className="text-xs text-muted-foreground hover:text-foreground underline cursor-pointer"
              >
                Failed to load more leads. Click to retry.
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
