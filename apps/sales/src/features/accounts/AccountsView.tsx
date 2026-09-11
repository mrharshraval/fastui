"use client";

import * as React from "react";
import { Search, X, MoreHorizontal } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { DeleteConfirmationDialog } from "@/components/ui/delete-confirmation-dialog";
import {
  DropdownMenu,
  DropdownMenuItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useSelection } from "@/shared/hooks/useSelection";
import { CompaniesTab } from "./components/CompaniesTab";
import { ContactsTab } from "./components/ContactsTab";
import { accountsApi } from "./api";
import type { CompanyModel, ContactModel } from "./types";

interface AccountsViewProps {
  initialCompanies?: CompanyModel[];
  initialContacts?: ContactModel[];
}

export function AccountsView({
  initialCompanies = [],
  initialContacts = [],
}: AccountsViewProps) {
  const [activeTab, setActiveTab] = React.useState<"companies" | "contacts">("companies");
  const [search, setSearch] = React.useState("");

  const [companies, setCompanies] = React.useState<CompanyModel[]>(initialCompanies);
  const [contacts, setContacts] = React.useState<ContactModel[]>(initialContacts);
  const [loadingCompanies, setLoadingCompanies] = React.useState(!initialCompanies.length);
  const [loadingContacts, setLoadingContacts] = React.useState(!initialContacts.length);

  // Fetch if not provided
  React.useEffect(() => {
    if (!initialCompanies.length) {
      accountsApi
        .listCompanies()
        .then(setCompanies)
        .catch(() => setCompanies([]))
        .finally(() => setLoadingCompanies(false));
    }
    if (!initialContacts.length) {
      accountsApi
        .listContacts()
        .then(setContacts)
        .catch(() => setContacts([]))
        .finally(() => setLoadingContacts(false));
    }
  }, [initialCompanies.length, initialContacts.length]);

  // Client filtering
  const filteredCompanies = React.useMemo(() => {
    const q = search.toLowerCase().trim();
    if (!q) return companies;
    return companies.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        (c.industry ?? "").toLowerCase().includes(q) ||
        (c.domain ?? "").toLowerCase().includes(q)
    );
  }, [companies, search]);

  const filteredContacts = React.useMemo(() => {
    const q = search.toLowerCase().trim();
    if (!q) return contacts;
    return contacts.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        (c.email ?? "").toLowerCase().includes(q) ||
        (c.company ?? "").toLowerCase().includes(q)
    );
  }, [contacts, search]);

  // Selections
  const companySelection = useSelection<string>();
  const contactSelection = useSelection<string>();

  const isCompanyTab = activeTab === "companies";
  const activeSelection = isCompanyTab ? companySelection : contactSelection;
  const currentItems = isCompanyTab ? filteredCompanies : filteredContacts;
  const currentItemIds = React.useMemo(() => currentItems.map((i) => i.id), [currentItems]);

  const isSelectionMode = activeSelection.selectedCount > 0;
  const isAllSelected = activeSelection.isAllSelected(currentItemIds);
  const isSomeSelected = activeSelection.isSomeSelected(currentItemIds);
  const toggleAll = React.useCallback(
    () => activeSelection.toggleAll(currentItemIds),
    [activeSelection, currentItemIds]
  );

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

  const handleDeleteSelected = () => {
    if (isCompanyTab) {
      if (companySelection.selectedCount === 0) return;
      const count = companySelection.selectedCount;
      const ids = Array.from(companySelection.selectedIds);
      const numericIds = ids
        .map((id) => parseInt(id.replace(/[^0-9]/g, ""), 10))
        .filter((n) => !isNaN(n) && n > 0);

      setDeleteDialog({
        open: true,
        title: `Delete ${count} ${count === 1 ? "company" : "companies"}?`,
        itemName: `${count} selected ${count === 1 ? "company" : "companies"}`,
        warningText: "This action cannot be undone.",
        onConfirm: async () => {
          const prev = [...companies];
          setCompanies(companies.filter((c) => !companySelection.selectedIds.has(c.id)));
          companySelection.clearSelection();
          if (numericIds.length > 0) {
            try {
              await accountsApi.deleteCompany(numericIds[0]); // Bulk delete uses /businesses endpoint
            } catch {
              setCompanies(prev);
            }
          }
        },
      });
    } else {
      if (contactSelection.selectedCount === 0) return;
      const count = contactSelection.selectedCount;
      const ids = Array.from(contactSelection.selectedIds);

      setDeleteDialog({
        open: true,
        title: `Delete ${count} ${count === 1 ? "contact" : "contacts"}?`,
        itemName: `${count} selected ${count === 1 ? "contact" : "contacts"}`,
        warningText: "This action cannot be undone.",
        onConfirm: async () => {
          const prev = [...contacts];
          setContacts(contacts.filter((c) => !contactSelection.selectedIds.has(c.id)));
          contactSelection.clearSelection();
          try {
            await Promise.all(
              ids.map((id) => {
                const numId = parseInt(id.replace(/[^0-9]/g, ""), 10);
                return !isNaN(numId) && numId > 0
                  ? accountsApi.deleteContact(numId)
                  : Promise.resolve();
              })
            );
          } catch {
            setContacts(prev);
          }
        },
      });
    }
  };

  const handleSingleDeleteCompany = (id: string, name?: string) => {
    setDeleteDialog({
      open: true,
      title: "Delete company?",
      itemName: name || "this company",
      warningText: "This action cannot be undone.",
      onConfirm: async () => {
        const prev = [...companies];
        setCompanies((p) => p.filter((c) => c.id !== id));
        const numId = parseInt(id.replace(/[^0-9]/g, ""), 10);
        if (!isNaN(numId) && numId > 0) {
          try {
            await accountsApi.deleteCompany(numId);
          } catch {
            setCompanies(prev);
          }
        }
      },
    });
  };

  const handleSingleDeleteContact = (id: string, name?: string) => {
    setDeleteDialog({
      open: true,
      title: "Delete contact?",
      itemName: name || "this contact",
      warningText: "This action cannot be undone.",
      onConfirm: async () => {
        const prev = [...contacts];
        setContacts((p) => p.filter((c) => c.id !== id));
        const numId = parseInt(id.replace(/[^0-9]/g, ""), 10);
        if (!isNaN(numId) && numId > 0) {
          try {
            await accountsApi.deleteContact(numId);
          } catch {
            setContacts(prev);
          }
        }
      },
    });
  };

  const initials = (name: string) =>
    name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);

  return (
    <>
      {/* MOBILE VIEW (< md) */}
      <div className="flex flex-col w-full md:hidden pb-16">
        <div className="sticky top-0 z-10 bg-background flex items-center justify-between px-4 pt-4 pb-2">
          <h1 className="text-xl font-bold tracking-tight text-foreground">Accounts</h1>
        </div>

        <div className="relative z-0 px-4 pt-2 pb-4 bg-background">
          <div className="relative w-full group/search">
            <Search
              size={16}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors"
            />
            <input
              type="text"
              placeholder={activeTab === "companies" ? "Search companies…" : "Search contacts…"}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-10 w-full pl-10 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
            />
          </div>
        </div>

        <div className="sticky top-0 z-30 bg-background/95 backdrop-blur-md px-4 py-2 border-b border-border/30 flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => {
              setActiveTab("companies");
              setSearch("");
            }}
            className={`h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer shrink-0 whitespace-nowrap ${
              activeTab === "companies"
                ? "bg-primary text-primary-foreground font-semibold"
                : "text-muted-foreground hover:text-foreground font-medium"
            }`}
          >
            Companies ({companies.length})
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab("contacts");
              setSearch("");
            }}
            className={`h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer shrink-0 whitespace-nowrap ${
              activeTab === "contacts"
                ? "bg-primary text-primary-foreground font-semibold"
                : "text-muted-foreground hover:text-foreground font-medium"
            }`}
          >
            Contacts ({contacts.length})
          </button>
        </div>

        <div className="flex flex-col w-full divide-y divide-border/30">
          {activeTab === "companies" ? (
            loadingCompanies ? (
              Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="flex flex-col gap-2 py-3.5 px-4">
                  <Skeleton className="h-4 w-36 rounded" />
                  <Skeleton className="h-3 w-28 rounded" />
                  <Skeleton className="h-3 w-20 rounded" />
                </div>
              ))
            ) : filteredCompanies.length === 0 ? (
              <div className="py-20 text-center text-sm text-muted-foreground">
                No companies found.
              </div>
            ) : (
              filteredCompanies.map((c) => (
                <div
                  key={c.id}
                  className="flex items-start justify-between py-3.5 px-4 active:bg-accent/40 transition-colors"
                >
                  <div className="flex flex-col min-w-0 pr-3 flex-1">
                    <div className="font-semibold text-[15px] text-foreground truncate leading-tight">
                      {c.name}
                    </div>
                    <div className="text-xs text-muted-foreground truncate mt-1">
                      {c.industry || "General Industry"}
                    </div>
                    <div className="text-xs text-muted-foreground truncate mt-0.5">
                      {c.domain ?? "—"} • {c.leads_count ?? 0} leads
                    </div>
                  </div>

                  <div className="shrink-0 flex items-center justify-center">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <button
                          type="button"
                          aria-label="Company options"
                          className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer shrink-0"
                        >
                          <MoreHorizontal size={18} />
                        </button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-44">
                        <DropdownMenuItem
                          onClick={() => handleSingleDeleteCompany(c.id, c.name)}
                          className="flex items-center min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] text-destructive hover:bg-destructive-muted"
                        >
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              ))
            )
          ) : loadingContacts ? (
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="flex flex-col gap-2 py-3.5 px-4">
                <Skeleton className="h-4 w-36 rounded" />
                <Skeleton className="h-3 w-28 rounded" />
                <Skeleton className="h-3 w-20 rounded" />
              </div>
            ))
          ) : filteredContacts.length === 0 ? (
            <div className="py-20 text-center text-sm text-muted-foreground">
              No contacts found.
            </div>
          ) : (
            filteredContacts.map((c) => (
              <div
                key={c.id}
                className="flex items-start justify-between py-3.5 px-4 active:bg-accent/40 transition-colors"
              >
                <div className="flex flex-col min-w-0 pr-3 flex-1">
                  <div className="flex items-center gap-2 font-semibold text-[15px] text-foreground truncate leading-tight">
                    <Avatar className="size-5 rounded-full shrink-0">
                      <AvatarFallback className="text-[10px] font-semibold bg-accent text-foreground rounded-full">
                        {initials(c.name)}
                      </AvatarFallback>
                    </Avatar>
                    <span className="truncate">{c.name}</span>
                  </div>
                  <div className="text-xs text-muted-foreground truncate mt-1">
                    {c.company ?? "—"} {c.role ? `• ${c.role}` : ""}
                  </div>
                  <div className="text-xs text-muted-foreground truncate mt-0.5">
                    {c.email ?? "—"}
                  </div>
                </div>

                <div className="shrink-0 flex items-center justify-center">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button
                        type="button"
                        aria-label="Contact options"
                        className="flex items-center justify-center size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent/60 active:scale-95 transition-all cursor-pointer shrink-0"
                      >
                        <MoreHorizontal size={18} />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-44">
                      <DropdownMenuItem
                        onClick={() => handleSingleDeleteContact(c.id, c.name)}
                        className="flex items-center min-h-9 px-2.5 rounded-xl cursor-pointer text-[13px] font-[500] text-destructive hover:bg-destructive-muted"
                      >
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* DESKTOP VIEW (>= md) */}
      <div className="hidden md:flex flex-col gap-8 px-8 lg:px-12 xl:px-16 pt-14 pb-8 max-w-[1600px] w-full mx-auto">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xl font-bold tracking-tight text-foreground">Accounts</h2>
          <div className="flex items-center gap-3">
            <div className="relative group/search">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground group-focus-within/search:text-foreground transition-colors"
              />
              <input
                type="text"
                placeholder={activeTab === "companies" ? "Search companies..." : "Search contacts..."}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="h-9 w-44 sm:w-56 pl-9 pr-4 rounded-full bg-accent/50 hover:bg-accent/80 focus:bg-accent focus:ring-2 focus:ring-foreground/20 text-sm font-medium text-foreground focus:outline-none transition-all placeholder:text-muted-foreground"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between min-h-9">
          {!isSelectionMode ? (
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => {
                  setActiveTab("companies");
                  setSearch("");
                }}
                className={`h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer ${
                  activeTab === "companies"
                    ? "bg-secondary text-foreground font-semibold"
                    : "text-muted-foreground hover:text-foreground font-medium"
                }`}
              >
                Companies ({companies.length})
              </button>
              <button
                type="button"
                onClick={() => {
                  setActiveTab("contacts");
                  setSearch("");
                }}
                className={`h-9 px-3.5 rounded-full text-sm transition-colors cursor-pointer ${
                  activeTab === "contacts"
                    ? "bg-secondary text-foreground font-semibold"
                    : "text-muted-foreground hover:text-foreground font-medium"
                }`}
              >
                Contacts ({contacts.length})
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-between w-full animate-in fade-in duration-150">
              <div className="flex items-center gap-2">
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
                  {activeSelection.selectedCount} selected
                </span>
                <button
                  type="button"
                  onClick={activeSelection.clearSelection}
                  className="flex items-center justify-center size-7 rounded-full hover:bg-accent text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                  title="Clear selection"
                >
                  <X size={20} />
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-col -ml-12 w-[calc(100%+3rem)] overflow-x-auto">
          {activeTab === "companies" ? (
            <CompaniesTab
              companies={filteredCompanies}
              selectedCompanies={companySelection.selectedIds}
              onToggleCompany={companySelection.toggle}
              onToggleAll={toggleAll}
              isAllSelected={isAllSelected}
              isSomeSelected={isSomeSelected}
              loading={loadingCompanies}
              onDeleteSingle={handleSingleDeleteCompany}
            />
          ) : (
            <ContactsTab
              contacts={filteredContacts}
              selectedContacts={contactSelection.selectedIds}
              onToggleContact={contactSelection.toggle}
              onToggleAll={toggleAll}
              isAllSelected={isAllSelected}
              isSomeSelected={isSomeSelected}
              loading={loadingContacts}
              onDeleteSingle={handleSingleDeleteContact}
            />
          )}
        </div>
      </div>

      <DeleteConfirmationDialog
        open={deleteDialog.open}
        onOpenChange={(open) => setDeleteDialog((prev) => ({ ...prev, open }))}
        title={deleteDialog.title}
        itemName={deleteDialog.itemName}
        warningText={deleteDialog.warningText}
        onConfirm={deleteDialog.onConfirm}
      />
    </>
  );
}
