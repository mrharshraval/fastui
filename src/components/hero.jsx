"use client";

import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { HalftoneImageBackdrop } from "@/platform/visuals/rigs/HalftoneImageBackdrop";

const FRAME_TUNES = [
  {
    maxWidthPx: 767,
    previewDistance: 3.2,
    verticalAnchor: 0.5,
    verticalOffsetPx: 0,
    horizontalOffsetPx: 0,
  },
  {
    maxWidthPx: 1199,
    previewDistance: 3.2,
    verticalAnchor: 0.5,
    verticalOffsetPx: 0,
    horizontalOffsetPx: 0,
  },
  {
    maxWidthPx: Number.POSITIVE_INFINITY,
    previewDistance: 3.2,
    verticalAnchor: 0.5,
    verticalOffsetPx: 0,
    horizontalOffsetPx: 0,
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
    dashColor: 0x3c8aff, // cerulean — brand palette
    hoverDashColor: 0x0000ff, // yellow — brand palette hover accent
  },
  hover: {
    halftoneEnabled: true,
    halftonePowerShift: 0.25,
    halftoneRadius: 0.2,
    halftoneWidthShift: 0.4,
    lightEnabled: false,
    lightIntensity: 1.2,
    lightRadius: 0.25,
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

export function Hero() {
  return (
    <section className="relative min-h-[100vh] flex flex-col justify-center items-center px-8 md:px-16 lg:px-20 overflow-hidden bg-background" id="hero-root">

      {/* Background WebGL Canvas */}
      <div className="absolute inset-0 mx-auto max-w-none overflow-clip pointer-events-none z-0">
        <div
          aria-hidden="true"
          data-illustration="hero-star"
          className="absolute pointer-events-none transition-opacity duration-1000 ease-in-out opacity-100"
          style={{ inset: '-40px', width: 'calc(100% + 80px)', height: 'calc(100% + 80px)' }}
        >
          <HalftoneImageBackdrop
            imageUrl="/backdrop/hero-icon.png"
            settings={imageSettings}
            pointerRootSelector="#hero-root"
            priority={true}
            loading="eager"
          />
        </div>
      </div>

      {/* Glass Frost Effect */}
      <div className="absolute inset-0 pointer-events-none z-0 bg-background/10 backdrop-blur-[2px]" />

      {/* Content Overlay */}
      <div className="relative z-10 w-full max-w-4xl mx-auto flex flex-col items-center text-center space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-1000 ease-out pointer-events-none pt-20">

        {/* Pointer events auto re-enabled for content so users can select text/click buttons */}
        <div className="pointer-events-auto flex flex-col items-center space-y-8">

          <h1 className="text-4xl md:text-6xl lg:text-7xl font-medium tracking-tight leading-tight">
            Design that drives results.
          </h1>

          <p className="text-xl md:text-2xl text-muted-foreground font-medium max-w-2xl mx-auto">
            We build digital experiences for ambitious businesses.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            <Link href="/contact" className={cn(buttonVariants({ size: "default" }), "h-14 px-10 text-lg rounded-full transition-all")}>
              Get in touch
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
