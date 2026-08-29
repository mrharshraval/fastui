'use client';

import dynamic from 'next/dynamic';
import { type ReactNode } from 'react';

import { type ImageSessionSettings } from '../halftone/create-image-session';
import { VisualMount } from '../engine/VisualMount';

// The ONLY import() of the heavy video pipeline.
const HalftoneVideoScene = dynamic(
  () =>
    import('../halftone/HalftoneVideoScene').then(
      (module) => module.HalftoneVideoScene,
    ),
  { ssr: false },
);

export type HalftoneVideoBackdropProps = {
  videoUrl: string;
  settings: ImageSessionSettings;
  pointerRootSelector?: string;
  onFirstFrame?: () => void;
  poster?: ReactNode;
  priority?: boolean;
  loading?: 'lazy' | 'eager';
  detachFromLayout?: boolean;
  // Backdrops keep their artwork under reduced motion as a frozen frame.
  reducedMotionMode?: 'poster' | 'designed';
};

export function HalftoneVideoBackdrop({
  videoUrl,
  settings,
  pointerRootSelector,
  onFirstFrame,
  poster = null,
  priority = false,
  loading = 'lazy',
  detachFromLayout = false,
  reducedMotionMode = 'designed',
}: HalftoneVideoBackdropProps) {
  return (
    <VisualMount
      detachFromLayout={detachFromLayout}
      loading={loading}
      poster={poster}
      priority={priority}
      reducedMotion={reducedMotionMode}
    >
      <HalftoneVideoScene
        videoUrl={videoUrl}
        onFirstFrame={onFirstFrame}
        pointerRootSelector={pointerRootSelector}
        settings={settings}
      />
    </VisualMount>
  );
}
