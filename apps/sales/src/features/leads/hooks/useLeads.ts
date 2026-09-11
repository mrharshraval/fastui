import { useState, useCallback, useRef, useEffect } from "react";
import { leadsApi } from "../api";
import type { LeadModel, LeadFilterParams } from "../types";

export interface UseLeadsOptions {
  initialLeads?: LeadModel[];
  pageSize?: number;
  initialFilters?: LeadFilterParams;
}

export function useLeads({
  initialLeads = [],
  pageSize = 50,
  initialFilters = {},
}: UseLeadsOptions = {}) {
  const [leads, setLeads] = useState<LeadModel[]>(initialLeads);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(initialLeads.length >= pageSize);
  const [error, setError] = useState<string | null>(null);

  // In-memory record storage
  const leadsMapRef = useRef<Map<string, LeadModel>>(
    new Map(initialLeads.map((l) => [l.id, l]))
  );

  // Set of deleted IDs (both optimistic pending and confirmed) to prevent
  // in-flight or subsequent pagination queries from resurrecting deleted records.
  const deletedIdsRef = useRef<Set<string>>(new Set());

  // Server pagination offset tracker.
  // Reconciled on deletions to avoid offset drift and duplicate/missing pages.
  const serverOffsetRef = useRef<number>(initialLeads.length);

  // Active query sequence counter to discard stale out-of-order fetch responses
  const requestSeqRef = useRef(0);

  const abortControllerRef = useRef<AbortController | null>(null);
  const isFetchingRef = useRef(false);

  // Sync initial state if provided
  useEffect(() => {
    leadsMapRef.current = new Map(initialLeads.map((l) => [l.id, l]));
    deletedIdsRef.current.clear();
    serverOffsetRef.current = initialLeads.length;
    setLeads(initialLeads);
    setHasMore(initialLeads.length >= pageSize);
    setLoading(false);
  }, [initialLeads, pageSize]);

  const fetchLeads = useCallback(
    async (params?: LeadFilterParams, isInitial = false) => {
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
        const fetched = await leadsApi.list(
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
          leadsMapRef.current = new Map(validFetched.map((l) => [l.id, l]));
          serverOffsetRef.current = fetched.length;
          setLeads(validFetched);
        } else {
          for (const item of validFetched) {
            leadsMapRef.current.set(item.id, item);
          }
          serverOffsetRef.current += fetched.length;
          setLeads(Array.from(leadsMapRef.current.values()));
        }

        setHasMore(fetched.length === pageSize);
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        if (currentSeq === requestSeqRef.current) {
          setError(err instanceof Error ? err.message : "Failed to load leads.");
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
    fetchLeads(undefined, false);
  }, [hasMore, loading, loadingMore, fetchLeads]);

  const updateBulkStage = useCallback(
    async (businessIds: number[], stage: string) => {
      const prevLeads = Array.from(leadsMapRef.current.values());

      // Optimistic update
      const idSet = new Set(businessIds.map(String));
      for (const lead of prevLeads) {
        if (idSet.has(lead.id)) {
          leadsMapRef.current.set(lead.id, { ...lead, status: stage });
        }
      }
      setLeads(Array.from(leadsMapRef.current.values()));

      try {
        await leadsApi.updateBulkStage(businessIds, stage);
      } catch (err) {
        // Rollback on failure
        leadsMapRef.current = new Map(prevLeads.map((l) => [l.id, l]));
        setLeads(prevLeads);
        throw err;
      }
    },
    []
  );

  /**
   * Production-grade single deletion:
   * 1. Immediate optimistic UI removal & registration in deletedIdsRef
   * 2. Reconcile server pagination offset
   * 3. Server confirmation call
   * 4. Deterministic rollback on failure
   */
  const deleteSingle = useCallback(
    async (id: string): Promise<void> => {
      const existing = leadsMapRef.current.get(id);
      if (!existing) return;

      const prevList = Array.from(leadsMapRef.current.values());

      // Optimistic removal
      deletedIdsRef.current.add(id);
      leadsMapRef.current.delete(id);
      serverOffsetRef.current = Math.max(0, serverOffsetRef.current - 1);
      setLeads(Array.from(leadsMapRef.current.values()));

      const numId = parseInt(id.replace(/[^0-9]/g, ""), 10);
      if (isNaN(numId) || numId <= 0) {
        return;
      }

      try {
        await leadsApi.deleteSingle(numId);
      } catch (err) {
        // Rollback on failure
        deletedIdsRef.current.delete(id);
        leadsMapRef.current = new Map(prevList.map((l) => [l.id, l]));
        serverOffsetRef.current += 1;
        setLeads(prevList);
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
    async (businessIds: number[]): Promise<void> => {
      if (businessIds.length === 0) return;

      const prevLeads = Array.from(leadsMapRef.current.values());
      const ids = businessIds.map(String);
      const idSet = new Set(ids);
      let removedCount = 0;

      // Optimistic removal
      for (const id of idSet) {
        if (leadsMapRef.current.has(id)) {
          deletedIdsRef.current.add(id);
          leadsMapRef.current.delete(id);
          removedCount += 1;
        }
      }

      serverOffsetRef.current = Math.max(0, serverOffsetRef.current - removedCount);
      setLeads(Array.from(leadsMapRef.current.values()));

      try {
        await leadsApi.deleteBulk(businessIds);
      } catch (err) {
        // Rollback on failure
        for (const id of idSet) {
          deletedIdsRef.current.delete(id);
        }
        leadsMapRef.current = new Map(prevLeads.map((l) => [l.id, l]));
        serverOffsetRef.current += removedCount;
        setLeads(prevLeads);
        throw err;
      }
    },
    []
  );

  const refetch = useCallback(() => {
    return fetchLeads(undefined, true);
  }, [fetchLeads]);

  const updateLeadOptimistic = useCallback((id: string, updates: Partial<LeadModel>) => {
    const existing = leadsMapRef.current.get(id);
    if (existing) {
      const updated = { ...existing, ...updates };
      leadsMapRef.current.set(id, updated);
      setLeads(Array.from(leadsMapRef.current.values()));
    }
  }, []);

  const removeLeadsOptimistic = useCallback((ids: string[]) => {
    for (const id of ids) {
      deletedIdsRef.current.add(id);
      leadsMapRef.current.delete(id);
    }
    setLeads(Array.from(leadsMapRef.current.values()));
  }, []);

  return {
    leads,
    loading,
    loadingMore,
    hasMore,
    error,
    fetchLeads,
    loadMore,
    refetch,
    updateLeadOptimistic,
    removeLeadsOptimistic,
    updateBulkStage,
    deleteSingle,
    deleteBulk,
  };
}
