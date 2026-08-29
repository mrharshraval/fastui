'use client';

import { useAsyncResource } from './use-async-resource';

export function useAsyncVideo(
  loader: (() => Promise<HTMLVideoElement>) | null,
): HTMLVideoElement | null {
  return useAsyncResource(loader);
}
