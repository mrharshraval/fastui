"use client";

import * as React from "react";
import { X, Phone, Mail, Calendar, MessageSquare } from "lucide-react";
import type { FollowUpAction } from "../types";

interface TouchpointModalProps {
  action: FollowUpAction | null;
  onClose: () => void;
  onSave: (
    action: FollowUpAction,
    type: "call" | "email" | "meeting" | "note",
    outcome: string,
    nextDate: string
  ) => Promise<void>;
}

export function TouchpointModal({ action, onClose, onSave }: TouchpointModalProps) {
  const [outcome, setOutcome] = React.useState("");
  const [nextDate, setNextDate] = React.useState("Tomorrow");
  const [type, setType] = React.useState<"call" | "email" | "meeting" | "note">("call");
  const [submitting, setSubmitting] = React.useState(false);

  if (!action) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onSave(action, type, outcome, nextDate);
      onClose();
    } catch (err) {
      console.error("[TouchpointModal] Save failed:", err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-backdrop backdrop-blur-[1px] p-4 animate-in fade-in">
      <div className="bg-card border border-border/40 rounded-2xl max-w-md w-full p-6 shadow-modal flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-foreground">
              Log Touchpoint Outcome
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              {action.contactName} <span className="ml-1.5">{action.company}</span>
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground cursor-pointer"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-foreground">
              Touchpoint Type
            </label>
            <div className="grid grid-cols-4 gap-2">
              {[
                { id: "call", label: "Call", icon: Phone },
                { id: "email", label: "Email", icon: Mail },
                { id: "meeting", label: "Meeting", icon: Calendar },
                { id: "note", label: "Note", icon: MessageSquare },
              ].map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setType(t.id as any)}
                  className={`flex flex-col items-center gap-1 p-2 rounded-xl text-sm font-medium transition-all cursor-pointer ${
                    type === t.id
                      ? "bg-primary text-primary-foreground font-semibold shadow-none"
                      : "bg-accent text-muted-foreground hover:text-foreground hover:bg-accent/70"
                  }`}
                >
                  <t.icon className="size-4" />
                  <span>{t.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-foreground">
              Interaction Outcome
            </label>
            <textarea
              rows={3}
              placeholder="e.g. Connected on call, reviewed enterprise tier requirements, agreed to send revised SLA..."
              value={outcome}
              onChange={(e) => setOutcome(e.target.value)}
              className="w-full rounded-xl bg-accent/40 p-3 text-base text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring/30 resize-none border-none"
              required
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-semibold text-foreground">
              Next Follow-up Date
            </label>
            <div className="grid grid-cols-3 gap-2">
              {["Tomorrow", "In 2 days", "Next Week"].map((date) => (
                <button
                  key={date}
                  type="button"
                  onClick={() => setNextDate(date)}
                  className={`p-2 rounded-xl text-sm font-medium transition-all cursor-pointer ${
                    nextDate === date
                      ? "bg-primary text-primary-foreground font-semibold shadow-none"
                      : "bg-accent text-muted-foreground hover:text-foreground hover:bg-accent/70"
                  }`}
                >
                  {date}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-border/40">
            <button
              type="button"
              onClick={onClose}
              className="h-9 px-3 text-sm font-medium text-muted-foreground hover:text-foreground cursor-pointer transition-colors rounded-2xl hover:bg-accent"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="h-9 px-4 text-sm font-semibold rounded-2xl cursor-pointer bg-primary text-primary-foreground hover:bg-primary/90 transition-colors active:scale-[0.98] disabled:opacity-50"
            >
              {submitting ? "Saving…" : "Save & Update"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
