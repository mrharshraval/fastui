import * as React from "react";
import { cn } from "@/shared/lib/cn";
import type { BusinessDetail } from "../types";

export function isVerifiedPlaceUrl(url?: string | null): boolean {
  if (!url || typeof url !== "string") return false;
  const trimmed = url.trim();
  if (!trimmed.startsWith("http://") && !trimmed.startsWith("https://")) return false;

  if (
    trimmed.includes("/maps/search/") ||
    trimmed.includes("/search?") ||
    trimmed.includes("/search/") ||
    trimmed.includes("search/?api=1")
  ) {
    return false;
  }

  const isPlacePath = trimmed.includes("/maps/place/");
  const isCidUrl = /maps\?.*cid=\d+/i.test(trimmed) || /maps\/.*cid=\d+/i.test(trimmed);

  return isPlacePath || isCidUrl;
}

interface BusinessHeaderProps {
  business: BusinessDetail;
  onAction: (
    actionType: "website" | "call" | "email" | "whatsapp" | "location",
    targetValue: string
  ) => void;
  onOpenDemo: () => void;
  loadingDemo: boolean;
  hasDemo: boolean;
  onAddToLeads: () => void;
  addingToLeads: boolean;
}

export function BusinessHeader({
  business,
  onAction,
  onOpenDemo,
  loadingDemo,
  hasDemo,
  onAddToLeads,
  addingToLeads,
}: BusinessHeaderProps) {
  const initialLetter = (business.business_name || "B").charAt(0).toUpperCase();

  return (
    <div className="flex flex-col items-center w-full max-w-[540px] mx-auto text-center pt-2 md:pt-4 pb-6">
      {/* Circular Business Initial */}
      <div className="size-16 rounded-full bg-accent/70 text-foreground flex items-center justify-center text-xl font-bold tracking-tight shadow-none select-none">
        {initialLetter}
      </div>

      {/* Business Name */}
      <h2 className="text-xl md:text-2xl font-bold tracking-tight text-foreground mt-3">
        {business.business_name}
      </h2>

      {/* Location */}
      {business.location && (
        <p className="text-sm text-muted-foreground/80 mt-1">
          {business.location}
        </p>
      )}

      {/* Contact Actions Pills */}
      <div className="flex items-center justify-center gap-2 mt-6 md:mt-7 flex-wrap">
        {business.website && (
          <button
            type="button"
            onClick={() => onAction("website", business.website!)}
            className="h-8 px-4 rounded-full bg-accent/60 hover:bg-accent text-foreground text-sm font-medium transition-all active:scale-[0.98] cursor-pointer"
          >
            Website
          </button>
        )}

        {business.phone && (
          <button
            type="button"
            onClick={() => onAction("call", business.phone!)}
            className="h-8 px-4 rounded-full bg-accent/60 hover:bg-accent text-foreground text-sm font-medium transition-all active:scale-[0.98] cursor-pointer"
          >
            Phone
          </button>
        )}

        {business.email && (
          <button
            type="button"
            onClick={() => onAction("email", business.email!)}
            className="h-8 px-4 rounded-full bg-accent/60 hover:bg-accent text-foreground text-sm font-medium transition-all active:scale-[0.98] cursor-pointer"
          >
            Email
          </button>
        )}

        {(business.whatsapp || business.phone) && (
          <button
            type="button"
            onClick={() => onAction("whatsapp", business.whatsapp || business.phone!)}
            className="h-8 px-4 rounded-full bg-accent/60 hover:bg-accent text-foreground text-sm font-medium transition-all active:scale-[0.98] cursor-pointer"
          >
            WhatsApp
          </button>
        )}

        {isVerifiedPlaceUrl(business.google_maps_url) && (
          <button
            type="button"
            onClick={() => onAction("location", business.google_maps_url!)}
            className="h-8 px-4 rounded-full bg-accent/60 hover:bg-accent text-foreground text-sm font-medium transition-all active:scale-[0.98] cursor-pointer"
          >
            Location
          </button>
        )}

        {/* Demo Pill */}
        <button
          type="button"
          onClick={onOpenDemo}
          disabled={loadingDemo}
          className={cn(
            "h-8 px-4 rounded-full text-sm font-medium transition-all active:scale-[0.98] cursor-pointer inline-flex items-center justify-center",
            hasDemo
              ? "bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20"
              : "bg-accent/60 hover:bg-accent text-foreground"
          )}
        >
          <span>{loadingDemo ? "Creating…" : hasDemo ? "View" : "Create"}</span>
        </button>

        {/* Contextual Action: Approve (for unconverted prospects) */}
        {!business.is_lead && (
          <button
            type="button"
            onClick={onAddToLeads}
            disabled={addingToLeads}
            className="h-8 px-4 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium transition-all active:scale-[0.98] cursor-pointer inline-flex items-center justify-center disabled:opacity-50"
          >
            <span>{addingToLeads ? "Approving…" : "Approve"}</span>
          </button>
        )}
      </div>
    </div>
  );
}
