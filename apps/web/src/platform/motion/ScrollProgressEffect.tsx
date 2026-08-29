'use client';

import { type RefObject } from 'react';

import { useScrollProgress } from './use-scroll-progress';

export type ScrollProgressEffectProps = {
  enabled?: boolean;
  onScrollProgressAction: (progress: number) => void;
  scrollContainerRef: RefObject<HTMLElement | null>;
};

export function ScrollProgressEffect({
  enabled = true,
  onScrollProgressAction,
  scrollContainerRef,
}: ScrollProgressEffectProps): null {
  useScrollProgress(scrollContainerRef, onScrollProgressAction, { enabled });
  return null;
}
