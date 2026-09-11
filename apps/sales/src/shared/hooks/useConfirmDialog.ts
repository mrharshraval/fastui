import { useState, useCallback } from "react";

export interface ConfirmDialogState {
  isOpen: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isDestructive?: boolean;
  isLoading?: boolean;
  onConfirm: () => Promise<void> | void;
}

export function useConfirmDialog() {
  const [dialogState, setDialogState] = useState<ConfirmDialogState>({
    isOpen: false,
    title: "",
    description: "",
    confirmLabel: "Done",
    cancelLabel: "Cancel",
    isDestructive: false,
    isLoading: false,
    onConfirm: () => {},
  });

  const confirm = useCallback(
    (options: Omit<ConfirmDialogState, "isOpen" | "isLoading">) => {
      setDialogState({
        isOpen: true,
        isLoading: false,
        confirmLabel: "Done",
        cancelLabel: "Cancel",
        isDestructive: false,
        ...options,
      });
    },
    []
  );

  const close = useCallback(() => {
    setDialogState((prev) => ({ ...prev, isOpen: false, isLoading: false }));
  }, []);

  const handleConfirm = useCallback(async () => {
    try {
      setDialogState((prev) => ({ ...prev, isLoading: true }));
      await dialogState.onConfirm();
      close();
    } catch {
      setDialogState((prev) => ({ ...prev, isLoading: false }));
    }
  }, [dialogState, close]);

  return {
    isOpen: dialogState.isOpen,
    title: dialogState.title,
    description: dialogState.description,
    confirmLabel: dialogState.confirmLabel ?? "Done",
    cancelLabel: dialogState.cancelLabel ?? "Cancel",
    isDestructive: dialogState.isDestructive ?? false,
    isLoading: dialogState.isLoading ?? false,
    confirm,
    close,
    handleConfirm,
  };
}
