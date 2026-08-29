'use client';

import { styled } from '@linaria/react';
import { useCallback, useEffect, useRef } from 'react';

import { loadVisualVideo } from '../engine/load-visual-video';
import { useAsyncVideo } from '../engine/use-async-video';
import { useVisualRuntime } from '../engine/use-visual-runtime';
import {
  createImageSession,
  type ImageSessionSettings,
} from './create-image-session';

const SceneContainer = styled.div`
  height: 100%;
  width: 100%;
`;

export type HalftoneVideoSceneProps = {
  videoUrl: string;
  settings: ImageSessionSettings;
  pointerRootSelector?: string;
  onFirstFrame?: () => void;
};

export function HalftoneVideoScene({
  videoUrl,
  settings,
  pointerRootSelector,
  onFirstFrame,
}: HalftoneVideoSceneProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const { reducedMotion } = useVisualRuntime();

  const loader = useCallback(() => loadVisualVideo(videoUrl), [videoUrl]);
  const video = useAsyncVideo(loader);

  useEffect(() => {
    const container = containerRef.current;
    if (container === null || video === null) {
      return;
    }

    const session = createImageSession({
      container,
      image: video,
      settings,
      pointerRootSelector,
      reducedMotion,
      onFirstFrame,
    });

    return () => {
      session?.dispose();
    };
    // settings is a config record owned by the section; stable per mount.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [video, reducedMotion]);

  return <SceneContainer ref={containerRef} />;
}
