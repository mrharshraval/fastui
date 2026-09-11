import * as React from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/shared/lib/cn";
import { isVerifiedPlaceUrl } from "./BusinessHeader";
import type { BusinessDetail } from "../types";

interface DetailsTabProps {
  business: BusinessDetail;
  onAction: (
    actionType: "website" | "call" | "email" | "whatsapp" | "location",
    targetValue: string
  ) => void;
}

export function DetailsTab({ business, onAction }: DetailsTabProps) {
  const [showBusinessDetails, setShowBusinessDetails] = React.useState(true);
  const [showContactDetails, setShowContactDetails] = React.useState(true);

  const cityRegionCountry = [business.city, business.state, business.country]
    .filter(Boolean)
    .join(", ");

  const addressContent =
    business.address || cityRegionCountry ? (
      <div className="flex flex-col">
        {business.address && <span>{business.address}</span>}
        {cityRegionCountry && <span>{cityRegionCountry}</span>}
      </div>
    ) : null;

  const businessDetailsEntries = [
    { label: "Business name", value: business.business_name },
    business.category ? { label: "Category", value: business.category } : null,
    addressContent ? { label: "Address", value: addressContent } : null,
  ].filter(Boolean) as { label: string; value: React.ReactNode }[];

  const contactDetailsEntries = [
    business.website
      ? {
          label: "Website",
          value: (
            <button
              type="button"
              onClick={() => onAction("website", business.website!)}
              className="text-foreground hover:underline text-left cursor-pointer transition-colors"
            >
              {business.website.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "")}
            </button>
          ),
        }
      : null,
    business.phone
      ? {
          label: "Phone",
          value: (
            <button
              type="button"
              onClick={() => onAction("call", business.phone!)}
              className="text-foreground hover:underline text-left cursor-pointer transition-colors"
            >
              {business.phone}
            </button>
          ),
        }
      : null,
    business.email
      ? {
          label: "Email",
          value: (
            <button
              type="button"
              onClick={() => onAction("email", business.email!)}
              className="text-foreground hover:underline text-left cursor-pointer transition-colors"
            >
              {business.email}
            </button>
          ),
        }
      : null,
    business.whatsapp || business.phone
      ? {
          label: "WhatsApp",
          value: (
            <button
              type="button"
              onClick={() => onAction("whatsapp", business.whatsapp || business.phone!)}
              className="text-foreground hover:underline text-left cursor-pointer transition-colors"
            >
              {business.whatsapp || business.phone}
            </button>
          ),
        }
      : null,
    isVerifiedPlaceUrl(business.google_maps_url)
      ? {
          label: "Location",
          value: (
            <button
              type="button"
              onClick={() => onAction("location", business.google_maps_url!)}
              className="text-foreground hover:underline text-left cursor-pointer transition-colors"
            >
              View on Map
            </button>
          ),
        }
      : null,
  ].filter(Boolean) as { label: string; value: React.ReactNode }[];

  return (
    <div className="w-full max-w-[540px] mx-auto pb-8 flex flex-col animate-in fade-in duration-150">
      {/* Business Details Collapsible */}
      <div className="py-2 border-b border-border/40 first:border-t-0">
        <button
          type="button"
          onClick={() => setShowBusinessDetails((prev) => !prev)}
          className="flex items-center justify-between w-full text-left py-2 text-sm font-semibold text-foreground hover:text-foreground/80 transition-colors cursor-pointer group"
        >
          <span>Business details</span>
          <ChevronDown
            size={16}
            className={cn(
              "text-muted-foreground/60 transition-transform duration-200",
              showBusinessDetails && "rotate-180"
            )}
          />
        </button>

        {showBusinessDetails && (
          <div className="flex flex-col gap-3 text-sm pt-2 pb-3 animate-in fade-in slide-in-from-top-1 duration-200">
            {businessDetailsEntries.map((entry, i) => (
              <div key={i} className="flex flex-col gap-0.5">
                <span className="text-xs text-muted-foreground font-medium">
                  {entry.label}
                </span>
                <div className="text-foreground font-normal break-words">
                  {entry.value}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Contact Details Collapsible */}
      {contactDetailsEntries.length > 0 && (
        <div className="py-2 border-b border-border/40">
          <button
            type="button"
            onClick={() => setShowContactDetails((prev) => !prev)}
            className="flex items-center justify-between w-full text-left py-2 text-sm font-semibold text-foreground hover:text-foreground/80 transition-colors cursor-pointer group"
          >
            <span>Contact details</span>
            <ChevronDown
              size={16}
              className={cn(
                "text-muted-foreground/60 transition-transform duration-200",
                showContactDetails && "rotate-180"
              )}
            />
          </button>

          {showContactDetails && (
            <div className="flex flex-col gap-3 text-sm pt-2 pb-3 animate-in fade-in slide-in-from-top-1 duration-200">
              {contactDetailsEntries.map((entry, i) => (
                <div key={i} className="flex flex-col gap-0.5">
                  <span className="text-xs text-muted-foreground font-medium">
                    {entry.label}
                  </span>
                  <div className="text-foreground font-normal break-words">
                    {entry.value}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
