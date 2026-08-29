"use client";

import { HalftoneImageBackdrop } from "@/platform/visuals";

const FRAME_TUNES = [
  {
    maxWidthPx: 767,
    previewDistance: 3.2,
    verticalAnchor: 0,
    verticalOffsetPx: 0,
    horizontalOffsetPx: -60,
  },
  {
    maxWidthPx: 1199,
    previewDistance: 3.2,
    verticalAnchor: 0.5,
    verticalOffsetPx: 0,
    horizontalOffsetPx: -120,
  },
  {
    maxWidthPx: Number.POSITIVE_INFINITY,
    previewDistance: 3.2,
    verticalAnchor: 0.5,
    verticalOffsetPx: 224,
    horizontalOffsetPx: -151,
  },
];

function resolveFrameTune() {
  const viewportWidth =
    typeof window === 'undefined'
      ? Number.POSITIVE_INFINITY
      : window.innerWidth;
  const tune =
    FRAME_TUNES.find((candidate) => viewportWidth <= candidate.maxWidthPx) ??
    FRAME_TUNES[FRAME_TUNES.length - 1];
  return {
    previewDistance: tune.previewDistance,
    verticalAnchor: tune.verticalAnchor,
    verticalOffsetPx: tune.verticalOffsetPx,
    horizontalOffsetPx: tune.horizontalOffsetPx,
  };
}

const imageSettings = {
  previewDistance: 3.2,
  imageFit: 'width',
  verticalAnchor: 0.5,
  applyToDarkAreas: true,
  contrast: 1,
  halftone: {
    scale: 12,
    power: -0.07,
    width: 0.20,
    minimumTone: 0,
    dashColor: 0x4f46e5, // indigo-600 approx matching twenty's blue
    hoverDashColor: 0x4f46e5,
  },
  hover: {
    halftoneEnabled: false,
    halftonePowerShift: 0,
    halftoneRadius: 0.6,
    halftoneWidthShift: 0,
    lightEnabled: true,
    lightIntensity: 0.8,
    lightRadius: 0.14,
    lightVerticalFade: 0.5,
    fadeIn: 18,
    fadeOut: 7,
  },
  pointer: {
    follow: 0.38,
    velocityDamping: 0.82,
  },
  wave: {
    enabled: false,
    amount: 0,
    speed: 1,
  },
  responsiveFrame: resolveFrameTune,
  pointerExcludeSelector: '[data-halftone-exclude]',
  pointerScope: 'window',
};

export default function VisualTestPage() {
  return (
    <div className="w-full h-screen bg-neutral-950 flex flex-col relative overflow-hidden" id="visual-root">
      
      {/* Visual Canvas Area */}
      {/* Equivalent to SectionShell's data-background-layer data-full-bleed */}
      <div className="absolute inset-0 mx-auto max-w-none overflow-clip pointer-events-none z-0">
        {/* Equivalent to HeroBackdrop's BackdropMount (b15pyokf) */}
        <div 
          aria-hidden="true" 
          data-illustration="hero-bridge"
          className="absolute pointer-events-none transition-opacity duration-1000 ease-in-out opacity-100"
          style={{ inset: '-40px', width: 'calc(100% + 80px)', height: 'calc(100% + 80px)' }}
        >
          <HalftoneImageBackdrop
            imageUrl="/backdrop/butterfly.png"
            settings={imageSettings}
            pointerRootSelector="#visual-root"
            priority={true}
            loading="eager"
          />
        </div>
      </div>

      {/* Foreground Content */}
      <div className="relative z-10 p-12 text-white pointer-events-none">
        <h1 className="text-4xl font-semibold mb-4">Halftone Engine Test</h1>
        <p className="text-xl text-neutral-400 max-w-lg">
          This page tests the faithful reproduction of the WebGL fullscreen post-processing pipeline. 
          Move your mouse around to interact with the halftone shader.
        </p>
      </div>
    </div>
  );
}
