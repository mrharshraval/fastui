import { useCallback } from "react";
import { leadsApi } from "../api";
import type { LeadModel, LeadFilterParams } from "../types";
import { useInfiniteResource } from "@/shared/hooks/useInfiniteResource";

export interface UseLeadsOptions {
  initialLeads?: LeadModel[];
  pageSize?: number;
  params?: LeadFilterParams;
}

export function useLeads({
  initialLeads = [],
  pageSize = 20,
  params = {},
}: UseLeadsOptions = {}) {
  const {
    items: leads,
    loading,
    loadingMore,
    hasMore,
    error,
    loadMoreError,
    loadMore,
    refetch,
    updateItemOptimistic,
    removeItemOptimistic,
    restoreItems,
  } = useInfiniteResource<LeadModel, LeadFilterParams>({
    fetcher: (fetchParams, signal) => leadsApi.list(fetchParams, signal),
    pageSize,
    params,
    initialItems: initialLeads,
  });

  const updateBulkStage = useCallback(
    async (businessIds: number[], stage: string) => {
      const prevLeads = [...leads];
      const idSet = new Set(businessIds.map(String));
      for (const lead of prevLeads) {
        if (idSet.has(lead.id)) {
          updateItemOptimistic(lead.id, { status: stage });
        }
      }

      try {
        await leadsApi.updateBulkStage(businessIds, stage);
      } catch (err) {
        restoreItems(prevLeads);
        throw err;
      }
    },
    [leads, updateItemOptimistic, restoreItems]
  );

  /**
   * Production-grade single deletion:
   * 1. Immediate optimistic UI removal
   * 2. Server confirmation call
   * 3. Deterministic rollback on failure
   */
  const deleteSingle = useCallback(
    async (id: string): Promise<void> => {
      const existing = leads.find((l) => l.id === id);
      if (!existing) return;

      const prevList = [...leads];
      removeItemOptimistic(id);

      const numId = parseInt(id.replace(/[^0-9]/g, ""), 10);
      if (isNaN(numId) || numId <= 0) {
        return;
      }

      try {
        await leadsApi.deleteSingle(numId);
      } catch (err) {
        restoreItems(prevList);
        throw err;
      }
    },
    [leads, removeItemOptimistic, restoreItems]
  );

  /**
   * Production-grade bulk deletion:
   * 1. Immediate optimistic UI removal
   * 2. Server confirmation call
   * 3. Deterministic rollback on failure
   */
  const deleteBulk = useCallback(
    async (businessIds: number[]): Promise<void> => {
      if (businessIds.length === 0) return;

      const prevLeads = [...leads];
      const ids = businessIds.map(String);
      removeItemOptimistic(ids);

      try {
        await leadsApi.deleteBulk(businessIds);
      } catch (err) {
        restoreItems(prevLeads);
        throw err;
      }
    },
    [leads, removeItemOptimistic, restoreItems]
  );

  return {
    leads,
    loading,
    loadingMore,
    hasMore,
    error,
    loadMoreError,
    loadMore,
    refetch,
    updateLeadOptimistic: updateItemOptimistic,
    removeLeadsOptimistic: removeItemOptimistic,
    updateBulkStage,
    deleteSingle,
    deleteBulk,
  };
}

