"use client";

import * as React from "react";
import { X } from "lucide-react";
import { IOSWheelPicker } from "@/components/ui/ios-wheel-picker";
import { cn } from "@/shared/lib/cn";

interface NoteReminderSheetProps {
  activeSheet: "note" | "reminder" | null;
  onClose: () => void;
  keyboardHeight?: number;

  // Note props
  noteInput: string;
  onNoteInputChange: (val: string) => void;
  onSaveNote: () => void;
  submittingNote: boolean;

  // Reminder props
  reminderText: string;
  onReminderTextChange: (val: string) => void;
  reminderDate: string;
  reminderTime: string;
  onSaveReminder: () => void;
  submittingReminder: boolean;
  onCommitReminderDateTime: (d: string, t: string) => void;
}

export function NoteReminderSheet({
  activeSheet,
  onClose,
  keyboardHeight = 0,
  noteInput,
  onNoteInputChange,
  onSaveNote,
  submittingNote,
  reminderText,
  onReminderTextChange,
  reminderDate,
  reminderTime,
  onSaveReminder,
  submittingReminder,
  onCommitReminderDateTime,
}: NoteReminderSheetProps) {
  const [pickerStep, setPickerStep] = React.useState<"date" | "time" | null>(null);
  const [tempDate, setTempDate] = React.useState(reminderDate);
  const [tempTime, setTempTime] = React.useState(reminderTime);

  const noteTextareaRef = React.useRef<HTMLTextAreaElement | null>(null);
  const reminderTextareaRef = React.useRef<HTMLTextAreaElement | null>(null);

  React.useEffect(() => {
    if (!activeSheet) {
      setPickerStep(null);
    }
  }, [activeSheet]);

  React.useEffect(() => {
    if (activeSheet === "note" && noteTextareaRef.current) {
      const el = noteTextareaRef.current;
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 96)}px`;
    }
  }, [noteInput, activeSheet]);

  React.useEffect(() => {
    if (activeSheet === "reminder" && !pickerStep && reminderTextareaRef.current) {
      const el = reminderTextareaRef.current;
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 96)}px`;
    }
  }, [reminderText, activeSheet, pickerStep]);

  if (!activeSheet) return null;

  const handleDateControlClick = () => {
    if (pickerStep === "date") {
      setPickerStep(null);
      return;
    }
    if (!pickerStep) {
      setTempDate(reminderDate);
      setTempTime(reminderTime);
    }
    setPickerStep("date");
  };

  const handleTimeControlClick = () => {
    if (pickerStep === "time") {
      setPickerStep(null);
      return;
    }
    if (!pickerStep) {
      setTempDate(reminderDate);
      setTempTime(reminderTime);
    }
    setPickerStep("time");
  };

  const handleConfirmDate = () => {
    setPickerStep("time");
  };

  const handleConfirmTime = () => {
    onCommitReminderDateTime(tempDate, tempTime);
    setPickerStep(null);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center p-3.5 sm:p-4 md:pb-6 pointer-events-auto transition-[padding] duration-200 ease-out"
      style={{
        paddingBottom: keyboardHeight > 0 ? `${keyboardHeight + 12}px` : undefined,
      }}
    >
      <div
        onClick={onClose}
        className="fixed inset-0 bg-backdrop backdrop-blur-[1px] transition-opacity animate-in fade-in duration-200"
      />

      <div className="relative z-10 w-full max-w-md bg-card rounded-[28px] shadow-sheet border border-border/30 p-5 pt-3 pb-4 animate-in slide-in-from-bottom-6 duration-200 flex flex-col max-h-[calc(100dvh-3rem)] overflow-hidden">
        <div className="w-9 h-1 rounded-full bg-muted-foreground/25 mx-auto mb-3 shrink-0" />

        <div className="flex items-center justify-between pb-3 border-b border-border/20 shrink-0">
          <h2 className="text-base font-semibold text-foreground tracking-tight">
            {activeSheet === "note" ? "Note" : "Reminder"}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="size-7 rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent/60 transition-colors cursor-pointer"
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        {activeSheet === "note" && (
          <div className="flex flex-col pt-3 min-h-0 flex-1">
            <textarea
              ref={noteTextareaRef}
              autoFocus
              placeholder="Write a note…"
              value={noteInput}
              onChange={(e) => onNoteInputChange(e.target.value)}
              rows={1}
              className="w-full max-h-[96px] overflow-y-auto p-0 bg-transparent border-0 focus:outline-none focus:ring-0 text-sm text-foreground placeholder:text-muted-foreground/50 resize-none leading-relaxed overscroll-contain apple-scrollbar"
            />

            <div className="flex items-center justify-end pt-3 mt-2 border-t border-border/20 shrink-0">
              <button
                type="button"
                onClick={onSaveNote}
                disabled={!noteInput.trim() || submittingNote}
                className="h-8 px-4 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold text-xs transition-all cursor-pointer disabled:opacity-35 active:scale-[0.98]"
              >
                Save
              </button>
            </div>
          </div>
        )}

        {activeSheet === "reminder" && (
          <div className="flex flex-col pt-3 gap-3.5">
            {pickerStep ? (
              <div className="w-full flex flex-col items-center justify-center animate-in fade-in zoom-in-[0.98] duration-150 py-0.5">
                <IOSWheelPicker
                  mode={pickerStep}
                  date={tempDate}
                  time={tempTime}
                  onChange={(newDate, newTime) => {
                    setTempDate(newDate);
                    setTempTime(newTime);
                  }}
                />
              </div>
            ) : (
              <textarea
                ref={reminderTextareaRef}
                autoFocus
                placeholder="Follow up with Sarah…"
                value={reminderText}
                onChange={(e) => onReminderTextChange(e.target.value)}
                rows={1}
                className="w-full max-h-[96px] overflow-y-auto p-0 bg-transparent border-0 focus:outline-none focus:ring-0 text-sm text-foreground placeholder:text-muted-foreground/50 resize-none leading-relaxed overscroll-contain apple-scrollbar"
              />
            )}

            <div className="flex items-center justify-between pt-2 mt-1 border-t border-border/20 shrink-0">
              <div className="flex items-center gap-3 text-xs select-none">
                <button
                  type="button"
                  onClick={handleDateControlClick}
                  className={cn(
                    "transition-colors cursor-pointer p-0 bg-transparent border-0 focus:outline-none",
                    pickerStep === "date"
                      ? "text-primary font-semibold"
                      : "text-muted-foreground hover:text-foreground font-normal"
                  )}
                >
                  {(() => {
                    const targetDate = pickerStep ? tempDate : reminderDate;
                    try {
                      const [y, m, d] = targetDate.split("-").map(Number);
                      const dateObj = new Date(y, m - 1, d);
                      const today = new Date();
                      today.setHours(0, 0, 0, 0);
                      const checkDate = new Date(dateObj);
                      checkDate.setHours(0, 0, 0, 0);
                      const diffDays = Math.round(
                        (checkDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
                      );
                      if (diffDays === 0) return "Today";
                      if (diffDays === 1) return "Tomorrow";
                      const isCurrentYear = checkDate.getFullYear() === today.getFullYear();
                      return dateObj.toLocaleDateString("en-US", {
                        weekday: "short",
                        month: "short",
                        day: "numeric",
                        year: isCurrentYear ? undefined : "numeric",
                      });
                    } catch {
                      return targetDate;
                    }
                  })()}
                </button>

                <button
                  type="button"
                  onClick={handleTimeControlClick}
                  className={cn(
                    "transition-colors cursor-pointer p-0 bg-transparent border-0 focus:outline-none",
                    pickerStep === "time"
                      ? "text-primary font-semibold"
                      : "text-muted-foreground hover:text-foreground font-normal"
                  )}
                >
                  {(() => {
                    const targetTime = pickerStep ? tempTime : reminderTime;
                    try {
                      const [h, min] = targetTime.split(":").map(Number);
                      const timeObj = new Date();
                      timeObj.setHours(h, min);
                      return timeObj.toLocaleTimeString("en-US", {
                        hour: "numeric",
                        minute: "2-digit",
                      });
                    } catch {
                      return targetTime;
                    }
                  })()}
                </button>
              </div>

              {pickerStep === "date" ? (
                <button
                  type="button"
                  onClick={handleConfirmDate}
                  className="h-8 px-4 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold text-xs transition-all cursor-pointer active:scale-[0.98]"
                >
                  Confirm
                </button>
              ) : pickerStep === "time" ? (
                <button
                  type="button"
                  onClick={handleConfirmTime}
                  className="h-8 px-4 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold text-xs transition-all cursor-pointer active:scale-[0.98]"
                >
                  Confirm
                </button>
              ) : (
                <button
                  type="button"
                  onClick={onSaveReminder}
                  disabled={!reminderText.trim() || submittingReminder}
                  className="h-8 px-4 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold text-xs transition-all cursor-pointer disabled:opacity-35 active:scale-[0.98]"
                >
                  Save
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
