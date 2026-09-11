import * as React from "react";
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

interface LeadsMobileListProps {
  leads: LeadModel[];
  loading: boolean;
  loadingMore: boolean;
  loadMoreError: string | null;
  onLoadMore: () => void;
  onNavigate: (id: string) => void;
  onStatusChange: (id: string, status: string) => void;
  onDeleteSingle: (id: string, name: string) => void;
  onAction: (lead: LeadModel, type: "website" | "call" | "email" | "whatsapp", value: string) => void;
  sentinelRef: React.RefObject<HTMLDivElement | null>;
}

export function LeadsMobileList({
  leads,
  loading,
  loadingMore,
  loadMoreError,
  onLoadMore,
  onNavigate,
  onStatusChange,
  onDeleteSingle,
  onAction,
  sentinelRef,
}: LeadsMobileListProps) {
  return (
    <div className="flex flex-col w-full divide-y divide-border/30">
      {loading ? (
        Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex flex-col gap-2 py-3.5 px-4">
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-40 rounded" />
              <Skeleton className="size-4 rounded-full" />
            </div>
            <Skeleton className="h-3 w-28 rounded" />
            <Skeleton className="h-4 w-20 rounded-full mt-1" />
          </div>
        ))
      ) : leads.length === 0 ? (
        <div className="py-20 text-center text-sm text-muted-foreground">
          No leads found.
        </div>
      ) : (
        leads.map((lead) => (
          <div
            key={lead.id}
            onClick={() => onNavigate(lead.id)}
            className="flex flex-col gap-2 py-3.5 px-4 active:bg-accent/40 transition-colors cursor-pointer"
          >
            <div className="flex items-start justify-between">
              <div className="flex flex-col min-w-0 pr-3 flex-1">
                <div className="font-semibold text-[15px] text-foreground truncate leading-tight">
                  {lead.business_name}
                </div>
                {lead.location && (
                  <div className="text-xs text-muted-foreground truncate mt-0.5">
                    {lead.location}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-[11px] text-muted-foreground">
                  {formatDate(lead.created_at)}
                </span>
                <div onClick={(e) => e.stopPropagation()}>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button
                        type="button"
                        aria-label="Lead actions"
                        className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer"
                      >
                        <MoreHorizontal size={18} />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-48">
                      <div className="flex flex-col gap-1">
                        <DropdownMenuSub>
                          <DropdownMenuSubTrigger className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500]">
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
                                  {st}
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
                      </div>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </div>

            {/* Mobile Actionable Contact Buttons */}
            <div
              onClick={(e) => e.stopPropagation()}
              className="flex items-center gap-2 pt-1 overflow-x-auto no-scrollbar"
            >
              {lead.website && (
                <a
                  href={lead.website.startsWith("http") ? lead.website : `https://${lead.website}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => onAction(lead, "website", lead.website!)}
                  className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-accent/60 hover:bg-accent text-foreground transition-colors shrink-0"
                >
                  Website
                </a>
              )}

              {lead.phone && (
                <a
                  href={`tel:${lead.phone}`}
                  onClick={() => onAction(lead, "call", lead.phone!)}
                  className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-accent/60 hover:bg-accent text-foreground transition-colors shrink-0"
                >
                  Call
                </a>
              )}

              {lead.email && (
                <a
                  href={`mailto:${lead.email}`}
                  onClick={() => onAction(lead, "email", lead.email!)}
                  className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-accent/60 hover:bg-accent text-foreground transition-colors shrink-0"
                >
                  Email
                </a>
              )}

              {(lead.whatsapp || lead.phone) && (
                <button
                  type="button"
                  onClick={() => {
                    const targetPhone = (lead.whatsapp || lead.phone || "").replace(/[^0-9]/g, "");
                    window.open(`https://wa.me/${targetPhone}`, "_blank", "noopener,noreferrer");
                    onAction(lead, "whatsapp", lead.whatsapp || lead.phone!);
                  }}
                  className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-success-muted text-success hover:bg-success/20 transition-colors shrink-0 cursor-pointer"
                >
                  WhatsApp
                </button>
              )}
            </div>
          </div>
        ))
      )}

      {/* Infinite Scroll Sentinel & Indicator */}
      <div ref={sentinelRef} className="w-full py-2 flex flex-col items-center justify-center">
        {loadingMore && (
          <div className="flex flex-col gap-2 w-full py-1">
            {[1, 2].map((i) => (
              <div key={i} className="flex flex-col gap-2 py-3.5 px-4 animate-pulse">
                <div className="flex items-center justify-between">
                  <Skeleton className="h-4 w-36 rounded" />
                  <Skeleton className="size-4 rounded-full" />
                </div>
                <Skeleton className="h-3 w-24 rounded" />
                <Skeleton className="h-4 w-20 rounded-full mt-1" />
              </div>
            ))}
          </div>
        )}
        {loadMoreError && (
          <button
            type="button"
            onClick={onLoadMore}
            className="text-xs text-muted-foreground hover:text-foreground underline py-2 cursor-pointer"
          >
            Failed to load more. Tap to retry.
          </button>
        )}
      </div>
    </div>
  );
}
