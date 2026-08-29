"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import { HalftoneImageBackdrop } from "@/platform/visuals/rigs/HalftoneImageBackdrop";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

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

const getSettings = (dashColor, hoverDashColor) => ({
  previewDistance: 3.2,
  imageFit: 'cover',
  verticalAnchor: 0.5,
  applyToDarkAreas: true,
  contrast: 1,
  halftone: {
    scale: 12,
    power: -0.07,
    width: 0.20,
    minimumTone: 0,
    dashColor: dashColor,
    hoverDashColor: hoverDashColor,
    bgColor: 0xeef0f3,
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
});

const cards = [
  {
    id: "card-1",
    subtitle: "Platform + Apps",
    title: "Flexible windowing.\nA multitasker's delight.",
    imageUrl: "/backdrop/statue-2.jpg",
    dashColor: 0x3c8aff,
    hoverDashColor: 0x0000ff,
  },
  {
    id: "card-2",
    subtitle: "Intelligence",
    title: "Effortlessly helpful\nevery day.",
    imageUrl: "/backdrop/flower-1.png",
    dashColor: 0xff4f3c,
    hoverDashColor: 0xffd900,
  },
  {
    id: "card-3",
    subtitle: "Productivity",
    title: "Your workplace\ncan be any place.",
    imageUrl: "/backdrop/flower-2.jpg",
    dashColor: 0x22c55e,
    hoverDashColor: 0xa3e635,
  },
  {
    id: "card-4",
    subtitle: "Creativity",
    title: "Take your inner artist\nout and about.",
    imageUrl: "/backdrop/flower-3.png",
    dashColor: 0x9333ea,
    hoverDashColor: 0xf472b6,
  }
];

export function FeatureCarousel() {
  const scrollRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  const checkScroll = useCallback(() => {
    if (scrollRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
      setCanScrollLeft(scrollLeft > 0);
      setCanScrollRight(Math.ceil(scrollLeft + clientWidth) < scrollWidth);
    }
  }, []);

  useEffect(() => {
    checkScroll();
    const currentRef = scrollRef.current;
    if (currentRef) {
      currentRef.addEventListener("scroll", checkScroll);
      window.addEventListener("resize", checkScroll);
      return () => {
        currentRef.removeEventListener("scroll", checkScroll);
        window.removeEventListener("resize", checkScroll);
      };
    }
  }, [checkScroll]);

  const scroll = (direction) => {
    if (scrollRef.current) {
      const scrollAmount = direction === "left" ? -400 : 400;
      scrollRef.current.scrollBy({ left: scrollAmount, behavior: "smooth" });
    }
  };

  return (
    <section className="py-24 px-8 md:px-16 lg:px-20 bg-background overflow-hidden" id="feature-carousel-root">
      <div className="max-w-7xl mx-auto space-y-8">
        <h2 className="text-4xl md:text-5xl font-medium tracking-tight">
          Get to know our platform.
        </h2>

        <div className="relative">
          <div 
            ref={scrollRef}
            className="flex gap-6 xl:gap-10 overflow-x-auto snap-x snap-mandatory pb-8 pt-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
          >
            {cards.map((card, i) => (
              <div
                key={card.id}
                id={card.id}
                className="group relative flex-none w-full sm:w-[320px] md:w-[400px] h-[400px] sm:h-[450px] md:h-[550px] rounded-[40px] overflow-hidden snap-start shrink-0 cursor-pointer bg-muted/50"
              >
                {/* Background Video using Halftone effect */}
                <div className="absolute inset-0 z-0">
                  <div
                    aria-hidden="true"
                    data-illustration={card.id}
                    className="absolute inset-[-40px] pointer-events-none transition-opacity duration-1000 ease-in-out opacity-100"
                  >
                    <HalftoneImageBackdrop
                      imageUrl={card.imageUrl}
                      settings={getSettings(card.dashColor, card.hoverDashColor)}
                      pointerRootSelector={`#${card.id}`}
                      priority={i < 2}
                      loading={i < 2 ? "eager" : "lazy"}
                    />
                  </div>
                </div>
                
                {/* Frosted Glass Effect */}
                <div className="absolute inset-0 pointer-events-none z-10 bg-background/5 backdrop-blur-[1px]" />
                
                {/* Subtle overlay for text readability */}
                <div className="absolute inset-0 bg-background/20 group-hover:bg-background/10 transition-colors duration-500 pointer-events-none z-10" />

                {/* Content Overlay */}
                <div className="relative z-20 h-full p-6 sm:p-8 flex flex-col justify-end text-foreground pointer-events-none">
                  <div className="space-y-2 pointer-events-auto">
                    <p className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                      {card.subtitle}
                    </p>
                    <h3 className="text-2xl md:text-3xl font-medium tracking-tight whitespace-pre-line">
                      {card.title}
                    </h3>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {/* Carousel Navigation Buttons */}
          <div className="flex justify-end gap-3 mt-4 pr-4 sm:pr-0">
            <button
              onClick={() => scroll("left")}
              disabled={!canScrollLeft}
              className={cn(
                "h-10 w-10 rounded-full flex items-center justify-center border transition-all duration-300",
                canScrollLeft 
                  ? "bg-secondary text-secondary-foreground hover:bg-secondary/80 border-border cursor-pointer" 
                  : "bg-secondary/50 text-muted-foreground border-border/50 cursor-not-allowed opacity-50"
              )}
              aria-label="Scroll left"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              onClick={() => scroll("right")}
              disabled={!canScrollRight}
              className={cn(
                "h-10 w-10 rounded-full flex items-center justify-center border transition-all duration-300",
                canScrollRight 
                  ? "bg-secondary text-secondary-foreground hover:bg-secondary/80 border-border cursor-pointer" 
                  : "bg-secondary/50 text-muted-foreground border-border/50 cursor-not-allowed opacity-50"
              )}
              aria-label="Scroll right"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
