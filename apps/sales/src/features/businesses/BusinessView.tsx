"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, MoreHorizontal, Plus } from "lucide-react";
import { cn } from "@/shared/lib/cn";
import { localPartsToUtcIso, formatReminderDisplay } from "@/shared/lib/date";
import { businessApi } from "./api";
import { BusinessHeader } from "./components/BusinessHeader";
import { TimelineTab } from "./components/TimelineTab";
import { RemindersTab } from "./components/RemindersTab";
import { DetailsTab } from "./components/DetailsTab";
import { DemoDialog } from "./components/DemoDialog";
import { NoteReminderSheet } from "./components/NoteReminderSheet";
import { DeleteConfirmationDialog } from "@/components/ui/delete-confirmation-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { BusinessDetail, ActivityItem, ReminderItem } from "./types";

interface BusinessViewProps {
  initialBusiness: BusinessDetail | null;
  initialActivities?: ActivityItem[];
  initialReminders?: ReminderItem[];
}

export function BusinessView({
  initialBusiness,
  initialActivities = [],
  initialReminders = [],
}: BusinessViewProps) {
  const router = useRouter();

  const [business, setBusiness] = React.useState<BusinessDetail | null>(initialBusiness);
  const [activities, setActivities] = React.useState<ActivityItem[]>(initialActivities);
  const [reminders, setReminders] = React.useState<ReminderItem[]>(initialReminders);
  const [activeTab, setActiveTab] = React.useState<"activity" | "reminders" | "details">("activity");

  const [addingToLeads, setAddingToLeads] = React.useState(false);
  const [loadingDemo, setLoadingDemo] = React.useState(false);
  const [demoModalOpen, setDemoModalOpen] = React.useState(false);
  const [demoData, setDemoData] = React.useState<{
    token: string;
    demo_url: string;
    view_count: number;
  } | null>(null);

  // Sheet state
  const [activeSheet, setActiveSheet] = React.useState<"note" | "reminder" | null>(null);
  const [noteInput, setNoteInput] = React.useState("");
  const [submittingNote, setSubmittingNote] = React.useState(false);

  const [reminderText, setReminderText] = React.useState("");
  const [reminderDate, setReminderDate] = React.useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  });
  const [reminderTime, setReminderTime] = React.useState("10:00");
  const [submittingReminder, setSubmittingReminder] = React.useState(false);

  // Delete Dialog state
  const [deleteDialog, setDeleteDialog] = React.useState<{
    open: boolean;
    title: string;
    itemName?: string;
    warningText?: string;
    onConfirm: () => Promise<void> | void;
  }>({
    open: false,
    title: "",
    onConfirm: () => {},
  });

  // Client-side fetch demo if not provided
  React.useEffect(() => {
    if (business?.id) {
      businessApi.getDemo(business.id).then((demo) => {
        if (demo && demo.token) {
          setDemoData(demo);
        }
      });
    }
  }, [business?.id]);

  if (!business) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-3">
        <p className="text-sm text-muted-foreground">Business not found</p>
        <button
          type="button"
          onClick={() => router.back()}
          className="h-9 px-4 rounded-full bg-accent hover:bg-accent/80 text-foreground text-sm font-medium inline-flex items-center gap-1.5 transition-colors cursor-pointer"
        >
          <ArrowLeft size={16} />
          <span>Back</span>
        </button>
      </div>
    );
  }

  const handleAction = async (
    actionType: "website" | "call" | "email" | "whatsapp" | "location",
    targetValue: string
  ) => {
    let actionLabel = "";
    if (actionType === "website") {
      const url = targetValue.startsWith("http") ? targetValue : `https://${targetValue}`;
      window.open(url, "_blank", "noopener,noreferrer");
      actionLabel = "Visited website";
    } else if (actionType === "call") {
      window.location.href = `tel:${targetValue}`;
      actionLabel = "Call initiated";
    } else if (actionType === "email") {
      window.location.href = `mailto:${targetValue}`;
      actionLabel = "Email initiated";
    } else if (actionType === "whatsapp") {
      const cleanNum = targetValue.replace(/[^0-9]/g, "");
      window.open(`https://wa.me/${cleanNum}`, "_blank", "noopener,noreferrer");
      actionLabel = "WhatsApp opened";
    } else if (actionType === "location") {
      window.open(targetValue, "_blank", "noopener,noreferrer");
      actionLabel = "Viewed location";
    }

    const newActivity: ActivityItem = {
      id: `act-local-${Date.now()}`,
      user_name: "You",
      action: actionLabel,
      notes: targetValue,
      timestamp: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    };

    setActivities((prev) => [newActivity, ...prev]);

    try {
      const numId = parseInt(business.id.replace(/[^0-9]/g, ""), 10);
      if (!isNaN(numId) && numId > 0) {
        if (actionType === "website" || actionType === "location") {
          await businessApi.createActivity(numId, {
            type: actionType === "location" ? "location_viewed" : "website_visited",
            channel: actionType === "location" ? "maps" : "website",
            outcome: actionLabel,
            notes: targetValue,
          });
        } else {
          await businessApi.logOutreach(numId, actionType, targetValue, actionLabel);
        }
      }
    } catch {}
  };

  const handleAddToLeads = async () => {
    if (addingToLeads) return;
    setAddingToLeads(true);
    const numId = parseInt(business.id.replace(/[^0-9]/g, ""), 10);

    try {
      if (!isNaN(numId) && numId > 0) {
        await businessApi.promoteToLead(numId);
      }
      setBusiness((prev) => (prev ? { ...prev, is_lead: true } : null));
      setActivities((prev) => [
        {
          id: `act-promote-${Date.now()}`,
          user_name: "You",
          action: "Approved",
          notes: "Promoted to sales pipeline",
          timestamp: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric" }),
        },
        ...prev,
      ]);
    } catch {
    } finally {
      setAddingToLeads(false);
    }
  };

  const handleOpenDemo = async () => {
    if (demoData) {
      setDemoModalOpen(true);
      return;
    }
    const numId = parseInt(business.id.replace(/[^0-9]/g, ""), 10);
    if (isNaN(numId) || numId <= 0) return;

    setLoadingDemo(true);
    try {
      const res = await businessApi.generateDemo(numId, {});
      if (res && res.token) {
        setDemoData(res);
        setDemoModalOpen(true);
      }
    } catch (err) {
      console.error("Failed to generate demo:", err);
    } finally {
      setLoadingDemo(false);
    }
  };

  const handleDeleteBusiness = () => {
    const isLead = Boolean(business.is_lead);
    const label = isLead ? "lead" : "prospect";

    setDeleteDialog({
      open: true,
      title: `Delete ${label}?`,
      itemName: business.business_name || `this ${label}`,
      warningText: "This action cannot be undone.",
      onConfirm: async () => {
        const numId = parseInt(business.id.replace(/[^0-9]/g, ""), 10);
        if (!isNaN(numId) && numId > 0) {
          try {
            await businessApi.delete(numId);
          } catch {}
        }
        router.push(isLead ? "/leads" : "/prospects");
      },
    });
  };

  const handleSaveNote = async () => {
    if (!noteInput.trim() || submittingNote) return;
    setSubmittingNote(true);

    const text = noteInput.trim();
    const newAct: ActivityItem = {
      id: `act-note-${Date.now()}`,
      user_name: "You",
      action: "Note added",
      notes: text,
      timestamp: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    };

    setActivities((prev) => [newAct, ...prev]);
    setNoteInput("");
    setActiveSheet(null);
    setSubmittingNote(false);

    try {
      const numId = parseInt(business.id.replace(/[^0-9]/g, ""), 10);
      if (!isNaN(numId) && numId > 0) {
        await businessApi.createNote(numId, text);
      }
    } catch {}
  };

  const handleSaveReminder = async () => {
    if (!reminderText.trim() || submittingReminder) return;
    setSubmittingReminder(true);

    const text = reminderText.trim();
    const isoDue = localPartsToUtcIso(reminderDate, reminderTime);
    const formattedDue = formatReminderDisplay(isoDue);

    const newRem: ReminderItem = {
      id: `rem-${Date.now()}`,
      title: text,
      due_date: formattedDue,
      raw_due_at: isoDue,
      status: "pending",
      user_name: "You",
      timestamp: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    };

    setReminders((prev) => [newRem, ...prev]);

    setActivities((prev) => [
      {
        id: `act-rem-${Date.now()}`,
        user_name: "You",
        action: "Reminder set",
        notes: `${text} (${formattedDue})`,
        timestamp: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      },
      ...prev,
    ]);

    setReminderText("");
    setActiveSheet(null);
    setSubmittingReminder(false);

    try {
      const numId = parseInt(business.id.replace(/[^0-9]/g, ""), 10);
      if (!isNaN(numId) && numId > 0) {
        await businessApi.createReminder(numId, {
          title: text,
          due_at: isoDue,
        });
      }
    } catch {}
  };

  return (
    <div className="flex flex-col h-full w-full min-h-screen bg-background">
      {/* Mobile Header */}
      <div className="md:hidden sticky top-0 z-10 bg-background flex items-center justify-between px-4 pt-4 pb-2 border-b border-border/30">
        <button
          type="button"
          onClick={() => router.back()}
          className="flex items-center gap-1.5 h-8 px-3 rounded-full bg-accent/60 hover:bg-accent text-foreground text-xs font-medium transition-colors cursor-pointer shrink-0"
        >
          <ArrowLeft size={14} />
          <span>Back</span>
        </button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              aria-label="Options"
              className="size-8 rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent/80 transition-colors cursor-pointer"
            >
              <MoreHorizontal size={18} />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-36">
            <DropdownMenuItem
              onClick={handleDeleteBusiness}
              className="text-destructive font-medium text-xs cursor-pointer"
            >
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Desktop Main Container */}
      <div className="flex flex-col flex-1 px-4 md:px-8 lg:px-12 xl:px-16 pt-4 md:pt-14 pb-16 max-w-[1600px] mx-auto w-full">
        <div className="hidden md:flex items-center justify-between mb-8">
          <button
            type="button"
            onClick={() => router.back()}
            className="h-9 px-4 rounded-full bg-accent/60 hover:bg-accent text-foreground text-sm font-medium transition-colors cursor-pointer inline-flex items-center gap-1.5"
          >
            <ArrowLeft size={16} />
            <span>Back</span>
          </button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                aria-label="Options"
                className="size-9 rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent/80 transition-colors cursor-pointer"
              >
                <MoreHorizontal size={18} />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-36">
              <DropdownMenuItem
                onClick={handleDeleteBusiness}
                className="text-destructive font-medium text-xs cursor-pointer"
              >
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Business Identity */}
        <BusinessHeader
          business={business}
          onAction={handleAction}
          onOpenDemo={handleOpenDemo}
          loadingDemo={loadingDemo}
          hasDemo={Boolean(demoData)}
          onAddToLeads={handleAddToLeads}
          addingToLeads={addingToLeads}
        />

        {/* Tabs Bar */}
        <div className="w-full max-w-[540px] mx-auto mt-7 mb-6 pb-2.5 border-b border-border/30 flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 min-w-0">
            {(
              [
                { id: "activity", label: "Activity" },
                { id: "reminders", label: "Reminders" },
                { id: "details", label: "Details" },
              ] as const
            ).map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer shrink-0 whitespace-nowrap",
                  activeTab === tab.id
                    ? "bg-primary text-primary-foreground font-semibold"
                    : "text-muted-foreground hover:text-foreground font-medium"
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="shrink-0 flex items-center">
            {activeTab === "activity" && (
              <button
                type="button"
                onClick={() => setActiveSheet("note")}
                className="flex items-center justify-center size-8 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground active:scale-95 transition-all cursor-pointer"
                aria-label="Add note"
                title="Add note"
              >
                <Plus size={16} />
              </button>
            )}

            {activeTab === "reminders" && (
              <button
                type="button"
                onClick={() => setActiveSheet("reminder")}
                className="flex items-center justify-center size-8 rounded-full bg-primary hover:bg-primary/90 text-primary-foreground active:scale-95 transition-all cursor-pointer"
                aria-label="Add reminder"
                title="Add reminder"
              >
                <Plus size={16} />
              </button>
            )}
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === "activity" && (
          <TimelineTab
            activities={activities}
            onDeleteActivity={(act) => {
              setDeleteDialog({
                open: true,
                title: "Delete activity?",
                itemName: act.action,
                warningText: "This action cannot be undone.",
                onConfirm: async () => {
                  const prev = [...activities];
                  setActivities((p) => p.filter((a) => a.id !== act.id));
                  const numId = parseInt(act.id.replace(/[^0-9]/g, ""), 10);
                  if (!isNaN(numId) && numId > 0) {
                    try {
                      if (act.id.includes("note")) {
                        await businessApi.deleteNote(numId);
                      } else {
                        await businessApi.deleteActivity(numId);
                      }
                    } catch {
                      setActivities(prev);
                    }
                  }
                },
              });
            }}
          />
        )}

        {activeTab === "reminders" && (
          <RemindersTab
            reminders={reminders}
            onCompleteReminder={async (rem) => {
              setReminders((prev) => prev.filter((r) => r.id !== rem.id));
              const numId = parseInt(rem.id.replace(/[^0-9]/g, ""), 10);
              if (!isNaN(numId) && numId > 0) {
                try {
                  await businessApi.updateReminder(numId, { status: "completed" });
                } catch {}
              }
            }}
            onDeleteReminder={(rem) => {
              setDeleteDialog({
                open: true,
                title: "Delete reminder?",
                itemName: rem.title || "this reminder",
                warningText: "This action cannot be undone.",
                onConfirm: async () => {
                  const prev = [...reminders];
                  setReminders((p) => p.filter((r) => r.id !== rem.id));
                  const numId = parseInt(rem.id.replace(/[^0-9]/g, ""), 10);
                  if (!isNaN(numId) && numId > 0) {
                    try {
                      await businessApi.deleteReminder(numId);
                    } catch {
                      setReminders(prev);
                    }
                  }
                },
              });
            }}
          />
        )}

        {activeTab === "details" && (
          <DetailsTab business={business} onAction={handleAction} />
        )}
      </div>

      <NoteReminderSheet
        activeSheet={activeSheet}
        onClose={() => setActiveSheet(null)}
        noteInput={noteInput}
        onNoteInputChange={setNoteInput}
        onSaveNote={handleSaveNote}
        submittingNote={submittingNote}
        reminderText={reminderText}
        onReminderTextChange={setReminderText}
        reminderDate={reminderDate}
        reminderTime={reminderTime}
        onSaveReminder={handleSaveReminder}
        submittingReminder={submittingReminder}
        onCommitReminderDateTime={(d, t) => {
          setReminderDate(d);
          setReminderTime(t);
        }}
      />

      <DemoDialog
        open={demoModalOpen}
        onOpenChange={setDemoModalOpen}
        businessName={business.business_name}
        demoUrl={demoData?.demo_url}
        viewCount={demoData?.view_count}
      />

      <DeleteConfirmationDialog
        open={deleteDialog.open}
        onOpenChange={(open) => setDeleteDialog((prev) => ({ ...prev, open }))}
        title={deleteDialog.title}
        itemName={deleteDialog.itemName}
        warningText={deleteDialog.warningText}
        onConfirm={deleteDialog.onConfirm}
      />
    </div>
  );
}
