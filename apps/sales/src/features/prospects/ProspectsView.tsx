"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Search, Download } from "lucide-react";
import { prospectsApi } from "./api";
import { useProspects } from "./hooks/useProspects";
import { useSelection } from "@/shared/hooks/useSelection";
import { useInfiniteScroll } from "@/shared/hooks/useInfiniteScroll";
import { DeleteConfirmationDialog } from "@/components/ui/delete-confirmation-dialog";
import { ExportDialog } from "@/features/exports/components/ExportDialog";
import { ProspectsTable } from "./components/ProspectsTable";
import { ProspectsMobileList } from "./components/ProspectsMobileList";
import { ProspectsFilterBar, type ProspectFilterState } from "./components/ProspectsFilterBar";
import { ProspectsBulkBar } from "./components/ProspectsBulkBar";
import type { ProspectModel } from "./types";

interface ProspectsViewProps {
  initialProspects?: ProspectModel[];
}

export function ProspectsView({ initialProspects = [] }: ProspectsViewProps) {
  const router = useRouter();

  const [searchQuery, setSearchQuery] = React.useState("");
  const [statusTab, setStatusTab] = React.useState("all");
  const [filters, setFilters] = React.useState<ProspectFilterState>({
    qualification: "all",
    website: "all",
    source: "all",
  });

  const {
    prospects,
    loading,
    loadingMore,
    hasMore,
    error: loadMoreError,
    loadMore,
    updateProspectOptimistic,
    removeProspectsOptimistic,
    deleteSingle,
    deleteBulk,
    refetch,
  } = useProspects({
    initialProspects,
    pageSize: 50,
  });

  // Infinite scroll sentinels
  const { sentinelRef: mobileSentinelRef } = useInfiniteScroll({
    hasMore,
    isLoading: loading || loadingMore,
    onLoadMore: loadMore,
  });

  const { sentinelRef: desktopSentinelRef } = useInfiniteScroll({
    hasMore,
    isLoading: loading || loadingMore,
    onLoadMore: loadMore,
  });

  // Client-side filtering and sorting
  const filteredItems = React.useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    return prospects
      .filter((p) => {
        const matchesSearch =
          !q ||
          p.business_name.toLowerCase().includes(q) ||
          (p.location ?? "").toLowerCase().includes(q) ||
          (p.website ?? "").toLowerCase().includes(q) ||
          (p.phone ?? "").toLowerCase().includes(q) ||
          (p.email ?? "").toLowerCase().includes(q);

        const matchesStatusTab =
          statusTab === "all" || p.qualification_status === statusTab;

        const matchesFilterStatus =
          filters.qualification === "all" || p.qualification_status === filters.qualification;

        const matchesFilterWebsite =
          filters.website === "all" ||
          (filters.website === "has_website" && Boolean(p.website)) ||
          (filters.website === "no_website" && !p.website);

        const matchesFilterSource =
          filters.source === "all" || p.source === filters.source;

        return (
          matchesSearch &&
          matchesStatusTab &&
          matchesFilterStatus &&
          matchesFilterWebsite &&
          matchesFilterSource
        );
      })
      .sort((a, b) => {
        const timeA = new Date(a.created_at).getTime();
        const timeB = new Date(b.created_at).getTime();
        if (timeB !== timeA) return timeB - timeA;
        const numA = parseInt(a.id.replace(/[^0-9]/g, ""), 10) || 0;
        const numB = parseInt(b.id.replace(/[^0-9]/g, ""), 10) || 0;
        return numB - numA;
      });
  }, [prospects, searchQuery, statusTab, filters]);

  // Selection hook
  const {
    selectedIds,
    selectedCount,
    isAllSelected: checkAllSelected,
    isSomeSelected: checkSomeSelected,
    toggle,
    toggleAll: toggleAllIds,
    deselect,
    clearSelection,
  } = useSelection<string>();

  const isSelectionMode = selectedCount > 0;
  const visibleProspectIds = React.useMemo(() => filteredItems.map((p) => p.id), [filteredItems]);
  const isAllSelected = checkAllSelected(visibleProspectIds);
  const isSomeSelected = checkSomeSelected(visibleProspectIds);
  const toggleAll = React.useCallback(
    () => toggleAllIds(visibleProspectIds),
    [toggleAllIds, visibleProspectIds]
  );

  // Delete confirmation dialog state
  const [deleteDialog, setDeleteDialog] = React.useState<{
    open: boolean;
    title: string;
    itemName?: string;
    description?: React.ReactNode;
    warningText?: string;
    onConfirm: () => Promise<void> | void;
  }>({
    open: false,
    title: "",
    onConfirm: () => {},
  });

  // Export dialog state
  const [exportDialogOpen, setExportDialogOpen] = React.useState(false);

  const selectedNumericIds = React.useMemo(() => {
    return Array.from(selectedIds)
      .map((id: string) => parseInt(id.replace(/\D/g, ""), 10))
      .filter((n) => !isNaN(n) && n > 0);
  }, [selectedIds]);

  const activeExportFilters = React.useMemo(() => {
    const effStatus =
      statusTab !== "all"
        ? statusTab
        : filters.qualification !== "all"
        ? filters.qualification
        : undefined;
    return {
      search: searchQuery.trim() || undefined,
      stage: effStatus,
      source: filters.source !== "all" ? filters.source : undefined,
    };
  }, [searchQuery, statusTab, filters]);

  const exportFilterSummary = React.useMemo(() => {
    const summary: Array<{ label: string; value: string }> = [];
    if (searchQuery.trim()) {
      summary.push({ label: "Search", value: searchQuery.trim() });
    }
    const effStatus =
      statusTab !== "all"
        ? statusTab
        : filters.qualification !== "all"
        ? filters.qualification
        : null;
    if (effStatus) {
      summary.push({
        label: "Qualification",
        value: effStatus.charAt(0).toUpperCase() + effStatus.slice(1),
      });
    }
    if (filters.source !== "all") {
      summary.push({
        label: "Source",
        value: filters.source.charAt(0).toUpperCase() + filters.source.slice(1),
      });
    }
    return summary;
  }, [searchQuery, statusTab, filters]);

  // Action logger
  const handleAction = async (
    prospect: ProspectModel,
    actionType: "website" | "call" | "email" | "whatsapp",
    targetValue: string
  ) => {
    try {
      const numId = parseInt(prospect.id.replace(/[^0-9]/g, ""), 10);
      if (!isNaN(numId) && numId > 0) {
        if (actionType === "website") {
          await prospectsApi.logActivity(numId, {
            type: "website_visited",
            channel: "website",
            outcome: "Website visited",
            notes: targetValue,
          }).catch(() => {});
        } else {
          await prospectsApi.logOutreach(numId, {
            channel: actionType,
            recipient: targetValue,
            status: "initiated",
            notes: `${actionType} initiated`,
          }).catch(() => {});
        }
      }
    } catch {
      // Graceful fallback
    }
  };

  // Single Add to Leads
  const handleSingleAddToLeads = async (prospect: ProspectModel) => {
    const numId = parseInt(prospect.id.replace(/[^0-9]/g, ""), 10);
    removeProspectsOptimistic([prospect.id]);

    try {
      if (!isNaN(numId) && numId > 0) {
        await prospectsApi.promoteToLeads([numId]);
      }
    } catch {
      refetch();
    }
  };

  // Bulk Add to Leads
  const handleBulkAddToLeads = async () => {
    if (selectedIds.size === 0) return;
    const ids = Array.from(selectedIds);
    const numericIds = ids
      .map((id) => parseInt(id.replace(/[^0-9]/g, ""), 10))
      .filter((n) => !isNaN(n) && n > 0);

    removeProspectsOptimistic(ids);
    clearSelection();

    try {
      if (numericIds.length > 0) {
        await prospectsApi.promoteToLeads(numericIds);
      }
    } catch {
      refetch();
    }
  };

  // Qualification status changes
  const handleSingleQualify = async (id: string, status: string) => {
    updateProspectOptimistic(id, { qualification_status: status });
    const numId = parseInt(id.replace(/[^0-9]/g, ""), 10);
    if (!isNaN(numId) && numId > 0) {
      try {
        await prospectsApi.qualifySingle(numId, status);
      } catch {
        refetch();
      }
    }
  };

  const handleBulkQualify = async (status: string) => {
    if (selectedIds.size === 0) return;
    const ids = Array.from(selectedIds);
    const numericIds = ids
      .map((id) => parseInt(id.replace(/[^0-9]/g, ""), 10))
      .filter((n) => !isNaN(n) && n > 0);

    for (const id of ids) {
      updateProspectOptimistic(id, { qualification_status: status });
    }
    clearSelection();

    try {
      if (numericIds.length > 0) {
        await prospectsApi.updateBulkQualification(numericIds, status);
      }
    } catch {
      refetch();
    }
  };

  const handleDeleteSingle = (id: string, name: string) => {
    setDeleteDialog({
      open: true,
      title: "Delete prospect?",
      itemName: name,
      warningText: "This action cannot be undone.",
      onConfirm: async () => {
        // 1. Immediately clean selection if deleted item was selected
        deselect(id);
        // 2. Perform optimistic removal + server confirmation + rollback on failure
        await deleteSingle(id);
        // 3. Revalidate Next.js server prefetch / router cache seamlessly
        router.refresh();
      },
    });
  };

  const handleDeleteSelected = () => {
    if (selectedIds.size === 0) return;
    const count = selectedIds.size;
    const ids = Array.from(selectedIds);

    setDeleteDialog({
      open: true,
      title: `Delete ${count} ${count === 1 ? "prospect" : "prospects"}?`,
      itemName: `${count} selected ${count === 1 ? "prospect" : "prospects"}`,
      warningText: "This action cannot be undone.",
      onConfirm: async () => {
        // 1. Clear selection immediately
        clearSelection();
        // 2. Perform optimistic removal + server confirmation + rollback on failure
        await deleteBulk(ids);
        // 3. Revalidate Next.js server prefetch / router cache seamlessly
        router.refresh();
      },
    });
  };

  return (
    <>
      {/* MOBILE VIEW (< md) */}
      <div className="flex flex-col w-full md:hidden pb-16">
        <div className="sticky top-0 z-10 bg-background flex items-center justify-between px-4 pt-4 pb-2">
          <h1 className="text-xl font-bold tracking-tight text-foreground">Prospects</h1>
          <button
            type="button"
            onClick={() => setExportDialogOpen(true)}
            className="flex items-center gap-1.5 h-8 px-3 rounded-full bg-accent/60 hover:bg-accent text-xs font-medium text-foreground active:scale-95 transition-all cursor-pointer"
          >
            <Download size={13} />
            <span>Export</span>
          </button>
        </div>

        <div className="relative z-0 px-4 pt-2 pb-4 bg-background">
          <div className="relative w-full group/search">
            <Search
              size={16}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors"
            />
            <input
              type="text"
              placeholder="Search prospects…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-10 w-full pl-10 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
            />
          </div>
        </div>

        <div className="sticky top-0 z-30 bg-background/95 backdrop-blur-md px-4 py-2.5 border-b border-border/30 flex items-center justify-between gap-2">
          <ProspectsFilterBar
            statusTab={statusTab}
            onStatusTabChange={setStatusTab}
            filters={filters}
            onFilterChange={(k, v) => setFilters((prev) => ({ ...prev, [k]: v }))}
            onResetFilters={() =>
              setFilters({
                qualification: "all",
                website: "all",
                source: "all",
              })
            }
          />
        </div>

        <ProspectsMobileList
          prospects={filteredItems}
          loading={loading}
          loadingMore={loadingMore}
          loadMoreError={loadMoreError}
          onLoadMore={loadMore}
          onNavigate={(id) => router.push(`/business/${id}`)}
          onSingleAddToLeads={handleSingleAddToLeads}
          onSingleQualify={handleSingleQualify}
          onDeleteSingle={handleDeleteSingle}
          onAction={handleAction}
          sentinelRef={mobileSentinelRef}
        />
      </div>

      {/* DESKTOP VIEW (>= md) */}
      <div className="hidden md:flex flex-col gap-8 px-8 lg:px-12 xl:px-16 pt-14 pb-8 max-w-[1600px] w-full mx-auto">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold tracking-tight text-foreground">Prospects</h2>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setExportDialogOpen(true)}
              title="Export prospects as CSV"
              className="flex items-center gap-1.5 h-9 px-3.5 rounded-full bg-accent/50 hover:bg-accent text-muted-foreground hover:text-foreground text-xs font-medium transition-colors cursor-pointer"
            >
              <Download size={14} />
              <span>Export</span>
            </button>

            <div className="relative group/search">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors"
              />
              <input
                type="text"
                placeholder="Search prospects..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-9 w-44 sm:w-56 pl-9 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between min-h-9">
          {!isSelectionMode ? (
            <ProspectsFilterBar
              statusTab={statusTab}
              onStatusTabChange={setStatusTab}
              filters={filters}
              onFilterChange={(k, v) => setFilters((prev) => ({ ...prev, [k]: v }))}
              onResetFilters={() =>
                setFilters({
                  qualification: "all",
                  website: "all",
                  source: "all",
                })
              }
            />
          ) : (
            <ProspectsBulkBar
              selectedCount={selectedCount}
              onClearSelection={clearSelection}
              onBulkApprove={handleBulkAddToLeads}
              onBulkQualify={handleBulkQualify}
              onDeleteSelected={handleDeleteSelected}
              onExport={() => setExportDialogOpen(true)}
            />
          )}
        </div>

        <ProspectsTable
          prospects={filteredItems}
          selectedProspects={selectedIds}
          onToggleProspect={toggle}
          onToggleAll={toggleAll}
          isAllSelected={isAllSelected}
          isSomeSelected={isSomeSelected}
          loading={loading}
          loadingMore={loadingMore}
          hasMore={hasMore}
          loadMoreError={loadMoreError}
          onLoadMore={loadMore}
          onSingleAddToLeads={handleSingleAddToLeads}
          onSingleQualify={handleSingleQualify}
          onDeleteSingle={handleDeleteSingle}
          onAction={handleAction}
          sentinelRef={desktopSentinelRef}
        />
      </div>

      <DeleteConfirmationDialog
        open={deleteDialog.open}
        onOpenChange={(open) => setDeleteDialog((prev) => ({ ...prev, open }))}
        title={deleteDialog.title}
        itemName={deleteDialog.itemName}
        description={deleteDialog.description}
        warningText={deleteDialog.warningText}
        onConfirm={deleteDialog.onConfirm}
      />

      <ExportDialog
        open={exportDialogOpen}
        onOpenChange={setExportDialogOpen}
        exportType="prospects"
        selectedCount={selectedCount}
        selectedIds={selectedNumericIds}
        activeFilters={activeExportFilters}
        filterSummary={exportFilterSummary}
      />
    </>
  );
}
