import * as React from "react";
import { Check, Copy, ExternalLink } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

interface DemoDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  businessName?: string;
  demoUrl?: string;
  viewCount?: number;
}

export function DemoDialog({
  open,
  onOpenChange,
  businessName,
  demoUrl,
  viewCount = 0,
}: DemoDialogProps) {
  const [copiedLink, setCopiedLink] = React.useState(false);

  const handleCopy = async () => {
    if (!demoUrl) return;
    try {
      await navigator.clipboard.writeText(demoUrl);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    } catch {}
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle className="text-base font-semibold">Demo</DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            {businessName ? `Website demo for ${businessName}.` : "Website demo link."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3.5 py-1.5">
          <div className="flex items-center gap-2">
            <input
              type="text"
              readOnly
              value={demoUrl || ""}
              className="flex-1 h-9 px-3 text-xs rounded-xl border border-border/60 bg-muted/30 font-mono select-all focus:outline-none"
            />
            <button
              type="button"
              onClick={handleCopy}
              className="h-9 px-3.5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-medium inline-flex items-center gap-1.5 transition-all shrink-0 cursor-pointer active:scale-95"
            >
              {copiedLink ? (
                <>
                  <Check size={14} />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy size={14} />
                  <span>Copy Link</span>
                </>
              )}
            </button>
          </div>

          <div className="p-3 rounded-xl bg-muted/40 border border-border/30 text-xs text-muted-foreground flex items-center justify-between">
            <span>Status</span>
            <span className="font-medium text-foreground">
              {viewCount > 0
                ? `🔥 Viewed ${viewCount} ${viewCount === 1 ? "time" : "times"}`
                : "Not viewed yet"}
            </span>
          </div>
        </div>

        <DialogFooter className="flex items-center justify-between sm:justify-between w-full pt-1.5">
          {demoUrl && (
            <a
              href={demoUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="h-8 px-3.5 rounded-full bg-accent/60 hover:bg-accent text-foreground text-xs font-medium inline-flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <ExternalLink size={13} />
              <span>Preview</span>
            </a>
          )}
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="h-8 px-4 rounded-full bg-foreground text-background hover:bg-foreground/90 text-xs font-medium transition-colors cursor-pointer ml-auto"
          >
            Done
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
