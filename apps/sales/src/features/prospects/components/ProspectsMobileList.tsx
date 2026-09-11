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
import type { ProspectModel } from "../types";

interface ProspectsMobileListProps {
  prospects: ProspectModel[];
  loading: boolean;
  loadingMore: boolean;
  loadMoreError: string | null;
  onLoadMore: () => void;
  onNavigate: (id: string) => void;
  onSingleAddToLeads: (prospect: ProspectModel) => void;
  onSingleQualify: (id: string, status: string) => void;
  onDeleteSingle: (id: string, name: string) => void;
  onAction: (
    prospect: ProspectModel,
    type: "website" | "call" | "email" | "whatsapp",
    value: string
  ) => void;
  sentinelRef: React.RefObject<HTMLDivElement | null>;
}

export function ProspectsMobileList({
  prospects,
  loading,
  loadingMore,
  loadMoreError,
  onLoadMore,
  onNavigate,
  onSingleAddToLeads,
  onSingleQualify,
  onDeleteSingle,
  onAction,
  sentinelRef,
}: ProspectsMobileListProps) {
  return (
    <div className="flex flex-col gap-3 px-4 pt-3 pb-8">
      {loading ? (
        Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="bg-card rounded-2xl border border-border/50 p-4 flex flex-col gap-2.5">
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-40 rounded" />
              <Skeleton className="size-4 rounded-full" />
            </div>
            <Skeleton className="h-3 w-28 rounded" />
            <Skeleton className="h-4 w-20 rounded-full mt-1" />
          </div>
        ))
      ) : prospects.length === 0 ? (
        <div className="py-20 text-center text-sm text-muted-foreground">
          No prospects found.
        </div>
      ) : (
        prospects.map((prospect) => (
          <div
            key={prospect.id}
            onClick={() => onNavigate(prospect.id)}
            className="bg-card text-card-foreground rounded-2xl border border-border/50 p-4 flex flex-col gap-2.5 transition-colors cursor-pointer hover:border-border active:bg-accent/30"
          >
            <div className="flex items-start justify-between">
              <div className="flex flex-col min-w-0 pr-3 flex-1">
                <div className="font-semibold text-[15px] text-foreground truncate leading-tight">
                  {prospect.business_name}
                </div>
                {prospect.location && (
                  <div className="text-xs text-muted-foreground truncate mt-0.5">
                    {prospect.location}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-[11px] text-muted-foreground">
                  {formatDate(prospect.created_at)}
                </span>
                <div onClick={(e) => e.stopPropagation()}>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button
                        type="button"
                        aria-label="Prospect actions"
                        className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer"
                      >
                        <MoreHorizontal size={18} />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-48">
                      <div className="flex flex-col gap-1">
                        <DropdownMenuItem
                          onClick={() => onSingleAddToLeads(prospect)}
                          className="flex items-center min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] text-primary"
                        >
                          <span>Approve</span>
                        </DropdownMenuItem>

                        <DropdownMenuSub>
                          <DropdownMenuSubTrigger className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500]">
                            Qualify
                          </DropdownMenuSubTrigger>
                          <DropdownMenuPortal>
                            <DropdownMenuSubContent className="w-40">
                              {["unqualified", "reviewing", "qualified", "disqualified"].map((st) => (
                                <DropdownMenuItem
                                  key={st}
                                  onClick={() => onSingleQualify(prospect.id, st)}
                                  className="flex items-center justify-between min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] capitalize"
                                >
                                  <span>{st}</span>
                                  {prospect.qualification_status === st && <Check className="size-3.5" />}
                                </DropdownMenuItem>
                              ))}
                            </DropdownMenuSubContent>
                          </DropdownMenuPortal>
                        </DropdownMenuSub>

                        <DropdownMenuItem
                          onClick={() => onDeleteSingle(prospect.id, prospect.business_name)}
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

            {/* Actionable Contact Buttons */}
            {(prospect.website || prospect.phone || prospect.email || prospect.whatsapp) && (
              <div
                onClick={(e) => e.stopPropagation()}
                className="flex items-center gap-2 pt-1 overflow-x-auto no-scrollbar"
              >
                {prospect.website && (
                  <a
                    href={prospect.website.startsWith("http") ? prospect.website : `https://${prospect.website}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => onAction(prospect, "website", prospect.website!)}
                    className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-accent/60 hover:bg-accent text-foreground transition-colors shrink-0"
                  >
                    Website
                  </a>
                )}

                {prospect.phone && (
                  <a
                    href={`tel:${prospect.phone}`}
                    onClick={() => onAction(prospect, "call", prospect.phone!)}
                    className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-accent/60 hover:bg-accent text-foreground transition-colors shrink-0"
                  >
                    Call
                  </a>
                )}

                {prospect.email && (
                  <a
                    href={`mailto:${prospect.email}`}
                    onClick={() => onAction(prospect, "email", prospect.email!)}
                    className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-accent/60 hover:bg-accent text-foreground transition-colors shrink-0"
                  >
                    Email
                  </a>
                )}

                {(prospect.whatsapp || prospect.phone) && (
                  <button
                    type="button"
                    onClick={() => {
                      const targetPhone = (prospect.whatsapp || prospect.phone || "").replace(/[^0-9]/g, "");
                      window.open(`https://wa.me/${targetPhone}`, "_blank", "noopener,noreferrer");
                      onAction(prospect, "whatsapp", prospect.whatsapp || prospect.phone!);
                    }}
                    className="inline-flex items-center h-7 px-2.5 rounded-full text-xs font-medium bg-success-muted text-success hover:bg-success/20 transition-colors shrink-0 cursor-pointer"
                  >
                    WhatsApp
                  </button>
                )}
              </div>
            )}
          </div>
        ))
      )}

      {/* Infinite Scroll Sentinel */}
      <div ref={sentinelRef} className="w-full py-2 flex flex-col items-center justify-center">
        {loadingMore && (
          <div className="flex flex-col gap-2 w-full py-1">
            {[1, 2].map((i) => (
              <div key={i} className="bg-card rounded-2xl border border-border/50 p-4 flex flex-col gap-2.5 animate-pulse">
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
