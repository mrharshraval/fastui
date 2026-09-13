import { useCallback } from "react";
import { prospectsApi } from "../api";
import type { ProspectModel, ProspectFilterParams } from "../types";
import { useInfiniteResource } from "@/shared/hooks/useInfiniteResource";

export interface UseProspectsOptions {
  initialProspects?: ProspectModel[];
  pageSize?: number;
  params?: ProspectFilterParams;
}

export function useProspects({
  initialProspects = [],
  pageSize = 20,
  params = {},
}: UseProspectsOptions = {}) {
  const {
    items: prospects,
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
  } = useInfiniteResource<ProspectModel, ProspectFilterParams>({
    fetcher: (fetchParams, signal) => prospectsApi.list(fetchParams, signal),
    pageSize,
    params,
    initialItems: initialProspects,
  });

  /**
   * Production-grade single deletion:
   * 1. Immediate optimistic UI removal
   * 2. Server confirmation call
   * 3. Deterministic rollback on failure
   */
  const deleteSingle = useCallback(
    async (id: string): Promise<void> => {
      const existing = prospects.find((p) => p.id === id);
      if (!existing) return;

      const prevList = [...prospects];
      removeItemOptimistic(id);

      const numId = parseInt(id.replace(/[^0-9]/g, ""), 10);
      if (isNaN(numId) || numId <= 0) {
        return;
      }

      try {
        await prospectsApi.deleteSingle(numId);
      } catch (err) {
        restoreItems(prevList);
        throw err;
      }
    },
    [prospects, removeItemOptimistic, restoreItems]
  );

  /**
   * Production-grade bulk deletion:
   * 1. Immediate optimistic UI removal
   * 2. Server confirmation call
   * 3. Deterministic rollback on failure
   */
  const deleteBulk = useCallback(
    async (ids: string[]): Promise<void> => {
      if (ids.length === 0) return;

      const prevList = [...prospects];
      removeItemOptimistic(ids);

      const numericIds = ids
        .map((id) => parseInt(id.replace(/[^0-9]/g, ""), 10))
        .filter((n) => !isNaN(n) && n > 0);

      if (numericIds.length === 0) {
        return;
      }

      try {
        await prospectsApi.deleteBulk(numericIds);
      } catch (err) {
        restoreItems(prevList);
        throw err;
      }
    },
    [prospects, removeItemOptimistic, restoreItems]
  );

  return {
    prospects,
    loading,
    loadingMore,
    hasMore,
    error,
    loadMoreError,
    loadMore,
    refetch,
    updateProspectOptimistic: updateItemOptimistic,
    removeProspectsOptimistic: removeItemOptimistic,
    deleteSingle,
    deleteBulk,
  };
}

