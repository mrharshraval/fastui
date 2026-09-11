import { useState, useCallback, useMemo } from "react";

export interface UseSelectionReturn<T extends string | number> {
  selectedIds: Set<T>;
  selectedCount: number;
  isSelected: (id: T) => boolean;
  toggle: (id: T) => void;
  toggleAll: (allIds: T[]) => void;
  select: (id: T) => void;
  deselect: (id: T) => void;
  selectAll: (allIds: T[]) => void;
  clearSelection: () => void;
  isAllSelected: (allIds: T[]) => boolean;
  isSomeSelected: (allIds: T[]) => boolean;
}

export function useSelection<T extends string | number>(initialSelection?: T[]): UseSelectionReturn<T> {
  const [selectedIds, setSelectedIds] = useState<Set<T>>(() => new Set(initialSelection ?? []));

  const isSelected = useCallback((id: T) => selectedIds.has(id), [selectedIds]);

  const toggle = useCallback((id: T) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const select = useCallback((id: T) => {
    setSelectedIds((prev) => {
      if (prev.has(id)) return prev;
      const next = new Set(prev);
      next.add(id);
      return next;
    });
  }, []);

  const deselect = useCallback((id: T) => {
    setSelectedIds((prev) => {
      if (!prev.has(id)) return prev;
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  }, []);

  const selectAll = useCallback((allIds: T[]) => {
    setSelectedIds(new Set(allIds));
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  const toggleAll = useCallback((allIds: T[]) => {
    setSelectedIds((prev) => {
      const allSelected = allIds.length > 0 && allIds.every((id) => prev.has(id));
      if (allSelected) {
        return new Set();
      }
      return new Set(allIds);
    });
  }, []);

  const isAllSelected = useCallback(
    (allIds: T[]) => allIds.length > 0 && allIds.every((id) => selectedIds.has(id)),
    [selectedIds]
  );

  const isSomeSelected = useCallback(
    (allIds: T[]) => allIds.length > 0 && allIds.some((id) => selectedIds.has(id)) && !isAllSelected(allIds),
    [selectedIds, isAllSelected]
  );

  return useMemo(
    () => ({
      selectedIds,
      selectedCount: selectedIds.size,
      isSelected,
      toggle,
      toggleAll,
      select,
      deselect,
      selectAll,
      clearSelection,
      isAllSelected,
      isSomeSelected,
    }),
    [selectedIds, isSelected, toggle, toggleAll, select, deselect, selectAll, clearSelection, isAllSelected, isSomeSelected]
  );
}
