import * as React from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal } from "lucide-react";
import type { ContactModel } from "../types";

interface ContactsTabProps {
  contacts: ContactModel[];
  selectedContacts: Set<string>;
  onToggleContact: (id: string) => void;
  onToggleAll: () => void;
  isAllSelected: boolean;
  isSomeSelected: boolean;
  loading: boolean;
  onDeleteSingle: (id: string, name: string) => void;
}

export function ContactsTab({
  contacts,
  selectedContacts,
  onToggleContact,
  onToggleAll,
  isAllSelected,
  isSomeSelected,
  loading,
  onDeleteSingle,
}: ContactsTabProps) {
  const isSelectionMode = selectedContacts.size > 0;

  const initials = (name: string) =>
    name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);

  return (
    <>
      {/* Header Row */}
      <div className="flex items-center group/header w-full pb-2.5 select-none min-w-[700px]">
        <div className="w-9 shrink-0 flex items-center justify-center">
          <div
            className={`transition-opacity duration-150 ${
              isSelectionMode
                ? "opacity-100"
                : "opacity-0 group-hover/header:opacity-100 hover:opacity-100"
            }`}
          >
            <Checkbox
              checked={isAllSelected ? true : isSomeSelected ? "indeterminate" : false}
              onCheckedChange={onToggleAll}
              aria-label="Select all visible contacts"
            />
          </div>
        </div>

        <div className="flex-1 grid grid-cols-12 gap-4 px-3 text-[14px] font-medium text-muted-foreground items-center">
          <div className="col-span-4">Name</div>
          <div className="col-span-3">Email</div>
          <div className="col-span-3">Company</div>
          <div className="col-span-2 text-right">Role</div>
        </div>
      </div>

      {/* Rows */}
      <div className="flex flex-col w-full min-w-[700px]">
        {loading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center w-full py-2.5">
              <div className="w-9 shrink-0 flex items-center justify-center">
                <Skeleton className="size-4 rounded" />
              </div>
              <div className="flex-1 grid grid-cols-12 gap-4 px-3 items-center">
                <Skeleton className="col-span-4 h-4 rounded" />
                <Skeleton className="col-span-3 h-4 rounded" />
                <Skeleton className="col-span-3 h-4 rounded" />
                <Skeleton className="col-span-2 h-4 rounded" />
              </div>
            </div>
          ))
        ) : contacts.length === 0 ? (
          <div className="py-16 text-center text-sm text-muted-foreground">
            No contacts found.
          </div>
        ) : (
          contacts.map((c, idx) => {
            const isSelected = selectedContacts.has(c.id);
            const prevSelected = idx > 0 && selectedContacts.has(contacts[idx - 1].id);
            const nextSelected =
              idx < contacts.length - 1 && selectedContacts.has(contacts[idx + 1].id);

            let selectionRounding = "rounded-xl";
            if (isSelected) {
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
              <div key={c.id} className="flex items-center group/row w-full my-[1px] relative">
                <div className="w-9 shrink-0 flex items-center justify-center">
                  <div
                    className={`transition-opacity duration-150 ${
                      isSelected
                        ? "opacity-100"
                        : "opacity-0 group-hover/row:opacity-100 hover:opacity-100"
                    }`}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={() => onToggleContact(c.id)}
                      aria-label={`Select ${c.name}`}
                    />
                  </div>
                </div>

                <div
                  onClick={() => onToggleContact(c.id)}
                  className={`flex-1 grid grid-cols-12 gap-4 px-3 py-3 text-sm items-center transition-colors cursor-pointer ${
                    isSelected
                      ? `bg-secondary text-foreground ${selectionRounding}`
                      : "hover:bg-accent/50 rounded-xl"
                  }`}
                >
                  <div className="col-span-4 flex items-center gap-2.5 truncate">
                    <Avatar className="size-6 rounded-full shrink-0">
                      <AvatarFallback className="text-[10px] font-semibold bg-accent text-foreground rounded-full">
                        {initials(c.name)}
                      </AvatarFallback>
                    </Avatar>
                    <span className="font-medium text-foreground truncate">{c.name}</span>
                  </div>
                  <div className="col-span-3 text-muted-foreground text-xs truncate">
                    {c.email ?? "—"}
                  </div>
                  <div className="col-span-3 text-muted-foreground text-xs truncate">
                    {c.company ?? "—"}
                  </div>
                  <div className="col-span-2 flex justify-end items-center gap-2">
                    <span className="text-xs text-muted-foreground truncate">{c.role ?? "Contact"}</span>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                        <button
                          type="button"
                          aria-label="Contact options"
                          className="size-7 rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent/80 transition-colors opacity-0 group-hover/row:opacity-100 cursor-pointer shrink-0"
                        >
                          <MoreHorizontal size={15} />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-36">
                        <DropdownMenuItem
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteSingle(c.id, c.name);
                          }}
                          className="text-destructive font-medium text-xs cursor-pointer"
                        >
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </>
  );
}
