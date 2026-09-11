"use client";

import * as React from "react";
import { Search, MoreHorizontal } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { DeleteConfirmationDialog } from "@/components/ui/delete-confirmation-dialog";
import {
  DropdownMenu,
  DropdownMenuItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { DealCard } from "./components/DealCard";
import { pipelineApi, type DealModel } from "./api";

const STAGES = ["Qualification", "Demo", "Proposal", "Negotiation", "Closed Won"];

interface PipelineViewProps {
  initialDeals?: DealModel[];
}

export function PipelineView({ initialDeals = [] }: PipelineViewProps) {
  const [deals, setDeals] = React.useState<DealModel[]>(initialDeals);
  const [loading, setLoading] = React.useState(!initialDeals.length);
  const [activeStage, setActiveStage] = React.useState("all");
  const [search, setSearch] = React.useState("");

  const [deleteDialog, setDeleteDialog] = React.useState<{
    open: boolean;
    title: string;
    itemName?: string;
    warningText?: string;
    onConfirm: () => Promise<void> | void;
  }>({
    open: false,
    title: "",
    onConfirm: () => {},
  });

  React.useEffect(() => {
    if (!initialDeals.length) {
      pipelineApi
        .list()
        .then(setDeals)
        .catch(() => setDeals([]))
        .finally(() => setLoading(false));
    }
  }, [initialDeals.length]);

  const byStage = (stage: string) => deals.filter((d) => d.stage === stage);

  const filteredDeals = deals.filter((d) => {
    const matchesSearch =
      !search || d.business_name.toLowerCase().includes(search.toLowerCase());
    const matchesStage = activeStage === "all" || d.stage === activeStage;
    return matchesSearch && matchesStage;
  });

  const handleStageChange = async (id: string, nextStage: string) => {
    const prev = [...deals];
    setDeals((p) => p.map((d) => (d.id === id ? { ...d, stage: nextStage } : d)));
    const numId = parseInt(id.replace(/[^0-9]/g, ""), 10);
    if (!isNaN(numId) && numId > 0) {
      try {
        await pipelineApi.updateStage(numId, nextStage);
      } catch {
        setDeals(prev);
      }
    }
  };

  const handleSingleDelete = (id: string, name?: string) => {
    setDeleteDialog({
      open: true,
      title: "Delete deal?",
      itemName: name || "this deal",
      warningText: "This action cannot be undone.",
      onConfirm: async () => {
        const prev = [...deals];
        setDeals((p) => p.filter((d) => d.id !== id));
        const numId = parseInt(id.replace(/[^0-9]/g, ""), 10);
        if (!isNaN(numId) && numId > 0) {
          try {
            await pipelineApi.delete(numId);
          } catch {
            setDeals(prev);
          }
        }
      },
    });
  };

  return (
    <>
      {/* MOBILE VIEW (< md) */}
      <div className="flex flex-col w-full md:hidden pb-16">
        <div className="sticky top-0 z-10 bg-background flex items-center justify-between px-4 pt-4 pb-2">
          <h1 className="text-xl font-bold tracking-tight text-foreground">Pipeline</h1>
        </div>

        <div className="relative z-0 px-4 pt-2 pb-4 bg-background">
          <div className="relative w-full group/search">
            <Search
              size={16}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors"
            />
            <input
              type="text"
              placeholder="Search deals…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-10 w-full pl-10 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
            />
          </div>
        </div>

        <div className="sticky top-0 z-30 bg-background/95 backdrop-blur-md px-4 py-2 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
          <button
            type="button"
            onClick={() => setActiveStage("all")}
            className={`h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer shrink-0 whitespace-nowrap ${
              activeStage === "all"
                ? "bg-primary text-primary-foreground font-semibold"
                : "text-muted-foreground hover:text-foreground font-medium"
            }`}
          >
            All Stages
          </button>
          {STAGES.map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => setActiveStage(st)}
              className={`h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer shrink-0 whitespace-nowrap ${
                activeStage === st
                  ? "bg-primary text-primary-foreground font-semibold"
                  : "text-muted-foreground hover:text-foreground font-medium"
              }`}
            >
              {st} ({byStage(st).length})
            </button>
          ))}
        </div>

        <div className="flex flex-col w-full divide-y divide-border/30">
          {loading ? (
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="flex flex-col gap-2 py-3.5 px-4">
                <Skeleton className="h-4 w-36 rounded" />
                <Skeleton className="h-3 w-28 rounded" />
                <Skeleton className="h-3 w-20 rounded" />
              </div>
            ))
          ) : filteredDeals.length === 0 ? (
            <div className="py-20 text-center text-sm text-muted-foreground">
              No deals found.
            </div>
          ) : (
            filteredDeals.map((deal) => (
              <div
                key={deal.id}
                className="flex items-start justify-between py-3.5 px-4 active:bg-accent/40 transition-colors"
              >
                <div className="flex flex-col min-w-0 pr-3 flex-1">
                  <div className="font-semibold text-[15px] text-foreground truncate leading-tight">
                    {deal.business_name}
                  </div>
                  <div className="text-xs text-muted-foreground truncate mt-1">
                    {deal.value ? `$${deal.value.toLocaleString("en-US")}` : "No value"}{" "}
                    {deal.probability ? `• ${deal.probability}% win probability` : ""}
                  </div>
                  <div className="text-xs text-muted-foreground truncate mt-0.5">
                    {deal.stage}
                  </div>
                </div>

                <div className="shrink-0 flex items-center justify-center">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button
                        type="button"
                        aria-label="Deal options"
                        className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer shrink-0"
                      >
                        <MoreHorizontal size={18} />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-44">
                      {STAGES.filter((s) => s !== deal.stage).map((st) => (
                        <DropdownMenuItem
                          key={st}
                          onClick={() => handleStageChange(deal.id, st)}
                          className="text-xs cursor-pointer"
                        >
                          Move to {st}
                        </DropdownMenuItem>
                      ))}
                      <DropdownMenuItem
                        onClick={() => handleSingleDelete(deal.id, deal.business_name)}
                        className="flex items-center min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] text-destructive hover:bg-destructive-muted"
                      >
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* DESKTOP VIEW (>= md) */}
      <div className="hidden md:flex flex-col gap-8 px-8 lg:px-12 xl:px-16 pt-14 pb-8 max-w-[1600px] w-full mx-auto">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold tracking-tight text-foreground">Pipeline</h2>
        </div>

        {/* Kanban Board */}
        <div className="flex gap-4 overflow-x-auto pb-4">
          {STAGES.map((stage) => (
            <div key={stage} className="flex flex-col gap-3 min-w-[240px] w-[240px] shrink-0">
              <div className="flex items-center justify-between px-1">
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {stage}
                </span>
                <Badge variant="secondary" className="text-xs rounded-full">
                  {byStage(stage).length}
                </Badge>
              </div>
              <div className="flex flex-col gap-2.5">
                {loading ? (
                  Array.from({ length: 2 }).map((_, i) => (
                    <Skeleton key={i} className="h-20 rounded-xl" />
                  ))
                ) : byStage(stage).length === 0 ? (
                  <div className="h-20 rounded-xl bg-accent/20 flex items-center justify-center">
                    <span className="text-xs text-muted-foreground">No deals</span>
                  </div>
                ) : (
                  byStage(stage).map((deal) => (
                    <DealCard
                      key={deal.id}
                      deal={deal}
                      stages={STAGES}
                      onStageChange={handleStageChange}
                      onDelete={handleSingleDelete}
                    />
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <DeleteConfirmationDialog
        open={deleteDialog.open}
        onOpenChange={(open) => setDeleteDialog((prev) => ({ ...prev, open }))}
        title={deleteDialog.title}
        itemName={deleteDialog.itemName}
        warningText={deleteDialog.warningText}
        onConfirm={deleteDialog.onConfirm}
      />
    </>
  );
}
