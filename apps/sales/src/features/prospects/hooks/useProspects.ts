import { useState, useCallback, useRef, useEffect } from "react";
import { prospectsApi } from "../api";
import type { ProspectModel, ProspectFilterParams } from "../types";

export interface UseProspectsOptions {
  initialProspects?: ProspectModel[];
  pageSize?: number;
  initialFilters?: ProspectFilterParams;
}

export function useProspects({
  initialProspects = [],
  pageSize = 50,
  initialFilters = {},
}: UseProspectsOptions = {}) {
  const [prospects, setProspects] = useState<ProspectModel[]>(initialProspects);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(initialProspects.length >= pageSize);
  const [error, setError] = useState<string | null>(null);

  // In-memory record storage
  const prospectsMapRef = useRef<Map<string, ProspectModel>>(
    new Map(initialProspects.map((p) => [p.id, p]))
  );

  // Set of deleted IDs (both optimistic pending and confirmed) to prevent
  // in-flight or subsequent pagination queries from resurrecting deleted records.
  const deletedIdsRef = useRef<Set<string>>(new Set());

  // Server pagination offset tracker.
  // Instead of relying on local loaded count (which drops on deletion),
  // this tracks the current server offset high-water mark, reconciled on deletions.
  const serverOffsetRef = useRef<number>(initialProspects.length);

  // Active query sequence counter to discard stale out-of-order fetch responses
  const requestSeqRef = useRef(0);

  const abortControllerRef = useRef<AbortController | null>(null);
  const isFetchingRef = useRef(false);

  useEffect(() => {
    prospectsMapRef.current = new Map(initialProspects.map((p) => [p.id, p]));
    deletedIdsRef.current.clear();
    serverOffsetRef.current = initialProspects.length;
    setProspects(initialProspects);
    setHasMore(initialProspects.length >= pageSize);
    setLoading(false);
  }, [initialProspects, pageSize]);

  const fetchProspects = useCallback(
    async (params?: ProspectFilterParams, isInitial = false) => {
      if (isFetchingRef.current && !isInitial) return;

      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;
      isFetchingRef.current = true;

      const currentSeq = ++requestSeqRef.current;

      if (isInitial) {
        setLoading(true);
        setError(null);
      } else {
        setLoadingMore(true);
      }

      const skip = isInitial ? 0 : serverOffsetRef.current;

      try {
        const fetched = await prospectsApi.list(
          {
            ...initialFilters,
            ...params,
            skip,
            limit: pageSize,
          },
          controller.signal
        );

        // Discard response if a newer query has superseded this one
        if (currentSeq !== requestSeqRef.current) {
          return;
        }

        // Filter out any items that were marked deleted locally
        const validFetched = fetched.filter((item) => !deletedIdsRef.current.has(item.id));

        if (isInitial) {
          prospectsMapRef.current = new Map(validFetched.map((p) => [p.id, p]));
          serverOffsetRef.current = fetched.length;
          setProspects(validFetched);
        } else {
          for (const item of validFetched) {
            prospectsMapRef.current.set(item.id, item);
          }
          serverOffsetRef.current += fetched.length;
          setProspects(Array.from(prospectsMapRef.current.values()));
        }

        setHasMore(fetched.length === pageSize);
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        if (currentSeq === requestSeqRef.current) {
          setError(err instanceof Error ? err.message : "Failed to load prospects.");
        }
      } finally {
        if (currentSeq === requestSeqRef.current) {
          isFetchingRef.current = false;
          if (isInitial) setLoading(false);
          setLoadingMore(false);
        }
      }
    },
    [pageSize, initialFilters]
  );

  const loadMore = useCallback(() => {
    if (!hasMore || loading || loadingMore || isFetchingRef.current) return;
    fetchProspects(undefined, false);
  }, [hasMore, loading, loadingMore, fetchProspects]);

  const refetch = useCallback(() => {
    return fetchProspects(undefined, true);
  }, [fetchProspects]);

  const updateProspectOptimistic = useCallback(
    (id: string, updates: Partial<ProspectModel>) => {
      const existing = prospectsMapRef.current.get(id);
      if (existing) {
        const updated = { ...existing, ...updates };
        prospectsMapRef.current.set(id, updated);
        setProspects(Array.from(prospectsMapRef.current.values()));
      }
    },
    []
  );

  const removeProspectsOptimistic = useCallback((ids: string[]) => {
    for (const id of ids) {
      deletedIdsRef.current.add(id);
      prospectsMapRef.current.delete(id);
    }
    setProspects(Array.from(prospectsMapRef.current.values()));
  }, []);

  /**
   * Production-grade single deletion:
   * 1. Immediate optimistic UI removal & registration in deletedIdsRef
   * 2. Reconcile server pagination offset
   * 3. Server confirmation call
   * 4. Deterministic rollback on failure
   */
  const deleteSingle = useCallback(
    async (id: string): Promise<void> => {
      const existing = prospectsMapRef.current.get(id);
      if (!existing) return;

      const prevList = Array.from(prospectsMapRef.current.values());

      // Optimistic removal
      deletedIdsRef.current.add(id);
      prospectsMapRef.current.delete(id);
      serverOffsetRef.current = Math.max(0, serverOffsetRef.current - 1);
      setProspects(Array.from(prospectsMapRef.current.values()));

      const numId = parseInt(id.replace(/[^0-9]/g, ""), 10);
      if (isNaN(numId) || numId <= 0) {
        return;
      }

      try {
        await prospectsApi.deleteSingle(numId);
      } catch (err) {
        // Rollback on failure
        deletedIdsRef.current.delete(id);
        prospectsMapRef.current = new Map(prevList.map((p) => [p.id, p]));
        serverOffsetRef.current += 1;
        setProspects(prevList);
        throw err;
      }
    },
    []
  );

  /**
   * Production-grade bulk deletion:
   * 1. Immediate optimistic UI removal & registration in deletedIdsRef
   * 2. Reconcile server pagination offset
   * 3. Server confirmation call
   * 4. Deterministic rollback on failure
   */
  const deleteBulk = useCallback(
    async (ids: string[]): Promise<void> => {
      if (ids.length === 0) return;

      const prevList = Array.from(prospectsMapRef.current.values());
      const idSet = new Set(ids);
      let removedCount = 0;

      for (const id of idSet) {
        if (prospectsMapRef.current.has(id)) {
          deletedIdsRef.current.add(id);
          prospectsMapRef.current.delete(id);
          removedCount += 1;
        }
      }

      serverOffsetRef.current = Math.max(0, serverOffsetRef.current - removedCount);
      setProspects(Array.from(prospectsMapRef.current.values()));

      const numericIds = ids
        .map((id) => parseInt(id.replace(/[^0-9]/g, ""), 10))
        .filter((n) => !isNaN(n) && n > 0);

      if (numericIds.length === 0) {
        return;
      }

      try {
        await prospectsApi.deleteBulk(numericIds);
      } catch (err) {
        // Rollback on failure
        for (const id of idSet) {
          deletedIdsRef.current.delete(id);
        }
        prospectsMapRef.current = new Map(prevList.map((p) => [p.id, p]));
        serverOffsetRef.current += removedCount;
        setProspects(prevList);
        throw err;
      }
    },
    []
  );

  return {
    prospects,
    loading,
    loadingMore,
    hasMore,
    error,
    fetchProspects,
    loadMore,
    refetch,
    updateProspectOptimistic,
    removeProspectsOptimistic,
    deleteSingle,
    deleteBulk,
  };
}
