import { useState, useCallback, useRef, useEffect } from "react";

export interface InfiniteResourceParams {
  skip?: number;
  limit?: number;
  cursor?: string | null;
  [key: string]: any;
}

export interface UseInfiniteResourceOptions<TItem, TParams extends InfiniteResourceParams> {
  fetcher: (params: TParams, signal?: AbortSignal) => Promise<TItem[]>;
  getItemId?: (item: TItem) => string;
  getItemCursor?: (item: TItem) => string | null;
  pageSize?: number;
  params?: Record<string, any>;
  initialItems?: TItem[];
  enabled?: boolean;
}

export interface UseInfiniteResourceResult<TItem> {
  items: TItem[];
  loading: boolean;
  loadingMore: boolean;
  hasMore: boolean;
  error: string | null;
  loadMoreError: string | null;
  loadMore: () => void;
  refetch: () => Promise<void>;
  updateItemOptimistic: (id: string, updates: Partial<TItem> | ((prev: TItem) => TItem)) => void;
  removeItemOptimistic: (idOrIds: string | string[]) => void;
  restoreItems: (itemsToRestore: TItem[]) => void;
}

export function useInfiniteResource<TItem, TParams extends InfiniteResourceParams = InfiniteResourceParams>({
  fetcher,
  getItemId = (item: any) => String(item.id),
  getItemCursor = (item: any) => {
    if (item && item.created_at && item.id) {
      return `${item.created_at}_${item.id}`;
    }
    return item && item.id ? String(item.id) : null;
  },
  pageSize = 20,
  params = {},
  initialItems = [],
  enabled = true,
}: UseInfiniteResourceOptions<TItem, TParams>): UseInfiniteResourceResult<TItem> {
  const [items, setItems] = useState<TItem[]>(initialItems);
  const [loading, setLoading] = useState<boolean>(initialItems.length === 0 && enabled);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [hasMore, setHasMore] = useState<boolean>(initialItems.length >= pageSize);
  const [error, setError] = useState<string | null>(null);
  const [loadMoreError, setLoadMoreError] = useState<string | null>(null);

  // In-memory keyed storage for strict deduplication
  const itemsMapRef = useRef<Map<string, TItem>>(
    new Map(initialItems.map((item) => [getItemId(item), item]))
  );

  // Set of deleted IDs (optimistically removed) to prevent resurrection
  const deletedIdsRef = useRef<Set<string>>(new Set());

  // Cursor tracking for cursor-based seek pagination
  const nextCursorRef = useRef<string | null>(
    initialItems.length > 0 ? getItemCursor(initialItems[initialItems.length - 1]) : null
  );

  // Offset tracker as fallback for offset-based callers
  const serverOffsetRef = useRef<number>(initialItems.length);

  // Request sequence tracking to discard superseded out-of-order responses
  const requestSeqRef = useRef<number>(0);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isFetchingRef = useRef<boolean>(false);

  // Keep fetcher and options in refs to avoid recreation cycles
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const getItemIdRef = useRef(getItemId);
  getItemIdRef.current = getItemId;

  const getItemCursorRef = useRef(getItemCursor);
  getItemCursorRef.current = getItemCursor;

  // Track serialized params to detect meaningful filter/search changes
  const serializedParams = JSON.stringify(params);
  const prevSerializedParamsRef = useRef(serializedParams);
  const isInitialMountRef = useRef(true);

  const fetchPage = useCallback(
    async (isInitial: boolean) => {
      if (!enabled) return;
      if (isFetchingRef.current && !isInitial) return;

      // Abort any in-flight request
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
        setLoadMoreError(null);
      }

      const cursor = isInitial ? null : nextCursorRef.current;
      const skip = isInitial ? 0 : serverOffsetRef.current;

      const queryParams = {
        ...params,
        skip,
        limit: pageSize,
        ...(cursor ? { cursor } : {}),
      } as unknown as TParams;

      try {
        const fetched = await fetcherRef.current(queryParams, controller.signal);

        // Discard if a newer request was dispatched
        if (currentSeq !== requestSeqRef.current) {
          return;
        }

        const validFetched = (fetched || []).filter(
          (item) => !deletedIdsRef.current.has(getItemIdRef.current(item))
        );

        if (isInitial) {
          const newMap = new Map<string, TItem>();
          for (const item of validFetched) {
            newMap.set(getItemIdRef.current(item), item);
          }
          itemsMapRef.current = newMap;
          serverOffsetRef.current = fetched.length;
          setItems(Array.from(newMap.values()));
        } else {
          for (const item of validFetched) {
            itemsMapRef.current.set(getItemIdRef.current(item), item);
          }
          serverOffsetRef.current += fetched.length;
          setItems(Array.from(itemsMapRef.current.values()));
        }

        if (fetched.length > 0) {
          nextCursorRef.current = getItemCursorRef.current(fetched[fetched.length - 1]);
        } else {
          nextCursorRef.current = null;
        }

        // Bounded pagination: stop when returned count is less than requested pageSize
        setHasMore(fetched.length === pageSize);
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }
        if (currentSeq === requestSeqRef.current) {
          const msg = err instanceof Error ? err.message : "Failed to load records.";
          if (isInitial) {
            setError(msg);
          } else {
            setLoadMoreError(msg);
          }
        }
      } finally {
        if (currentSeq === requestSeqRef.current) {
          isFetchingRef.current = false;
          if (isInitial) setLoading(false);
          setLoadingMore(false);
        }
      }
    },
    [enabled, pageSize, params]
  );

  // Initial fetch on mount or when filter/search params change
  useEffect(() => {
    if (!enabled) return;

    if (isInitialMountRef.current) {
      isInitialMountRef.current = false;
      // If no initial items were pre-provided, fetch page 0 immediately
      if (initialItems.length === 0) {
        fetchPage(true);
      }
      return;
    }

    if (prevSerializedParamsRef.current !== serializedParams) {
      prevSerializedParamsRef.current = serializedParams;
      // Reset cursor and fetch page 0 with new filter params
      nextCursorRef.current = null;
      serverOffsetRef.current = 0;
      deletedIdsRef.current.clear();
      fetchPage(true);
    }
  }, [enabled, serializedParams, initialItems.length, fetchPage]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const loadMore = useCallback(() => {
    if (!hasMore || loading || loadingMore || isFetchingRef.current) return;
    fetchPage(false);
  }, [hasMore, loading, loadingMore, fetchPage]);

  const refetch = useCallback(async () => {
    nextCursorRef.current = null;
    serverOffsetRef.current = 0;
    deletedIdsRef.current.clear();
    await fetchPage(true);
  }, [fetchPage]);

  const updateItemOptimistic = useCallback(
    (id: string, updates: Partial<TItem> | ((prev: TItem) => TItem)) => {
      const existing = itemsMapRef.current.get(id);
      if (existing) {
        const updated = typeof updates === "function" ? updates(existing) : { ...existing, ...updates };
        itemsMapRef.current.set(id, updated);
        setItems(Array.from(itemsMapRef.current.values()));
      }
    },
    []
  );

  const removeItemOptimistic = useCallback(
    (idOrIds: string | string[]) => {
      const idList = Array.isArray(idOrIds) ? idOrIds : [idOrIds];
      let removedCount = 0;
      for (const id of idList) {
        if (itemsMapRef.current.has(id)) {
          deletedIdsRef.current.add(id);
          itemsMapRef.current.delete(id);
          removedCount += 1;
        }
      }
      serverOffsetRef.current = Math.max(0, serverOffsetRef.current - removedCount);
      setItems(Array.from(itemsMapRef.current.values()));
    },
    []
  );

  const restoreItems = useCallback(
    (itemsToRestore: TItem[]) => {
      for (const item of itemsToRestore) {
        const id = getItemIdRef.current(item);
        deletedIdsRef.current.delete(id);
        itemsMapRef.current.set(id, item);
      }
      setItems(Array.from(itemsMapRef.current.values()));
    },
    []
  );

  return {
    items,
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
  };
}
