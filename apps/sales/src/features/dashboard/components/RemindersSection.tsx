"use client";

import * as React from "react";
import { Search, Plus, ListFilter, X } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import type { FollowUpAction } from "../types";

interface RemindersSectionProps {
  reminders: FollowUpAction[];
  onSelectAction: (action: FollowUpAction) => void;
  onDeleteReminders: (ids: string[]) => Promise<void>;
}

export function RemindersSection({
  reminders,
  onSelectAction,
  onDeleteReminders,
}: RemindersSectionProps) {
  const [search, setSearch] = React.useState("");
  const [tab, setTab] = React.useState<"all" | "pending" | "upcoming">("all");
  const [selected, setSelected] = React.useState<Set<string>>(new Set());

  const filtered = reminders.filter((f) => {
    const matchesSearch =
      !search ||
      f.contactName.toLowerCase().includes(search.toLowerCase()) ||
      f.company.toLowerCase().includes(search.toLowerCase()) ||
      f.nextAction.toLowerCase().includes(search.toLowerCase());
    const matchesTab =
      tab === "all"
        ? true
        : tab === "pending"
        ? f.bucket === "overdue" || f.bucket === "due_today"
        : f.bucket === "upcoming" || f.bucket === "waiting";
    return matchesSearch && matchesTab;
  });

  const visible = filtered.slice(0, 5);

  const isSelectionMode = selected.size > 0;
  const isAllSelected =
    visible.length > 0 && visible.every((item) => selected.has(item.id));
  const isSomeSelected =
    visible.some((item) => selected.has(item.id)) && !isAllSelected;

  const toggleAll = () => {
    if (isAllSelected) {
      const next = new Set(selected);
      visible.forEach((item) => next.delete(item.id));
      setSelected(next);
    } else {
      const next = new Set(selected);
      visible.forEach((item) => next.add(item.id));
      setSelected(next);
    }
  };

  const toggleItem = (id: string) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  };

  const handleDeleteSelected = async () => {
    const ids = Array.from(selected);
    setSelected(new Set());
    await onDeleteReminders(ids);
  };

  return (
    <div className="flex flex-col gap-3">
      {/* Section Header */}
      <div className="flex items-center justify-between mb-1 mt-2">
        <h2 className="text-xl font-bold tracking-tight text-foreground">Follow-ups</h2>
        <div className="flex items-center gap-3">
          <div className="relative group/search">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors"
            />
            <input
              type="text"
              placeholder="Search follow-ups…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-9 w-44 sm:w-56 pl-9 pr-4 rounded-full bg-secondary/50 hover:bg-secondary focus:bg-secondary border border-border/40 focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
            />
          </div>

          <button
            type="button"
            onClick={() => {
              const first = reminders[0];
              if (first) onSelectAction(first);
            }}
            title="Add Follow-up"
            className="flex items-center justify-center size-9 rounded-full bg-foreground text-background hover:bg-foreground/90 active:scale-95 transition-all cursor-pointer shrink-0"
          >
            <Plus size={18} strokeWidth={2.25} />
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between min-h-9">
        {!isSelectionMode ? (
          <>
            <div className="flex items-center gap-1.5">
              {(["all", "pending", "upcoming"] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setTab(t)}
                  className={`h-9 px-3.5 rounded-full text-sm capitalize transition-colors cursor-pointer ${
                    tab === t
                      ? "bg-muted text-foreground font-semibold"
                      : "text-muted-foreground hover:text-foreground font-medium"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>

            <div className="flex items-center">
              <button
                type="button"
                aria-label="Filter"
                className="relative flex items-center justify-center size-9 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent transition-colors cursor-pointer shrink-0"
              >
                <ListFilter size={20} />
              </button>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-between w-full animate-in fade-in duration-150">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  if (selected.size > 0) {
                    const firstId = Array.from(selected)[0];
                    const found = reminders.find((f) => f.id === firstId);
                    if (found) onSelectAction(found);
                  }
                }}
                className="h-9 px-4 rounded-full bg-secondary hover:bg-accent text-sm font-medium text-foreground transition-colors cursor-pointer"
              >
                Log Outcome
              </button>
              <button
                type="button"
                onClick={handleDeleteSelected}
                className="h-9 px-4 rounded-full border border-destructive/30 text-destructive hover:bg-destructive-muted text-sm font-medium transition-colors cursor-pointer"
              >
                Delete
              </button>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground font-normal">
                {selected.size} selected
              </span>
              <button
                type="button"
                onClick={() => setSelected(new Set())}
                className="flex items-center justify-center size-7 rounded-full hover:bg-accent text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                title="Clear selection"
              >
                <X size={20} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="flex flex-col -ml-12 w-[calc(100%+3rem)]">
        <div className="flex items-center group/header w-full pb-2.5 select-none">
          <div className="w-9 shrink-0 flex items-center justify-center">
            <div
              className={`transition-opacity duration-150 ${
                isSelectionMode
                  ? "opacity-100"
                  : "opacity-0 group-hover/header:opacity-100 hover:opacity-100"
              }`}
            >
              <Checkbox
                checked={
                  isAllSelected ? true : isSomeSelected ? "indeterminate" : false
                }
                onCheckedChange={toggleAll}
                aria-label="Select all visible reminders"
              />
            </div>
          </div>

          <div className="flex-1 grid grid-cols-12 gap-4 px-3 text-[14px] font-medium text-muted-foreground items-center">
            <div className="col-span-4">Contact</div>
            <div className="col-span-4">Next Action</div>
            <div className="col-span-2">Due Date</div>
            <div className="col-span-2 text-right">Status</div>
          </div>
        </div>

        <div className="flex flex-col w-full">
          {visible.length === 0 ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              No follow-ups found.
            </div>
          ) : (
            visible.map((action, idx) => {
              const isItemSelected = selected.has(action.id);
              const prevSelected =
                idx > 0 && selected.has(visible[idx - 1].id);
              const nextSelected =
                idx < visible.length - 1 && selected.has(visible[idx + 1].id);

              let selectionRounding = "rounded-xl";
              if (isItemSelected) {
                if (!prevSelected && nextSelected) {
                  selectionRounding = "rounded-t-xl border-b border-border/40";
                } else if (prevSelected && nextSelected) {
                  selectionRounding = "rounded-none border-b border-border/40";
                } else if (prevSelected && !nextSelected) {
                  selectionRounding = "rounded-b-xl";
                } else {
                  selectionRounding = "rounded-xl";
                }
              }

              return (
                <div
                  key={action.id}
                  className="flex items-center group/row w-full my-[1px] relative"
                >
                  <div className="w-9 shrink-0 flex items-center justify-center">
                    <div
                      className={`transition-opacity duration-150 ${
                        isItemSelected
                          ? "opacity-100"
                          : "opacity-0 group-hover/row:opacity-100 hover:opacity-100"
                      }`}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Checkbox
                        checked={isItemSelected}
                        onCheckedChange={() => toggleItem(action.id)}
                        aria-label={`Select ${action.contactName}`}
                      />
                    </div>
                  </div>

                  <div
                    onClick={() => onSelectAction(action)}
                    className={`flex-1 grid grid-cols-12 gap-4 px-3 py-3 text-sm items-center transition-colors cursor-pointer ${
                      isItemSelected
                        ? `bg-secondary text-foreground ${selectionRounding}`
                        : "hover:bg-accent/50 rounded-xl"
                    }`}
                  >
                    <div className="col-span-4 font-medium text-foreground truncate">
                      {action.contactName}
                      <span className="text-xs text-muted-foreground ml-2 font-normal">
                        {action.company}
                      </span>
                    </div>
                    <div className="col-span-4 text-muted-foreground text-xs truncate">
                      {action.nextAction}
                    </div>
                    <div className="col-span-2 text-muted-foreground text-xs truncate">
                      {action.dueDate}
                    </div>
                    <div className="col-span-2 flex justify-end">
                      {action.bucket === "overdue" ? (
                        <Badge
                          variant="destructive"
                          className="text-xs rounded-full px-2.5 py-0.5 font-normal"
                        >
                          Overdue
                        </Badge>
                      ) : action.bucket === "due_today" ? (
                        <Badge
                          variant="warning"
                          className="text-xs rounded-full px-2.5 py-0.5 font-normal"
                        >
                          Due Today
                        </Badge>
                      ) : (
                        <Badge
                          variant="secondary"
                          className="text-xs rounded-full px-2.5 py-0.5 font-normal"
                        >
                          Upcoming
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
