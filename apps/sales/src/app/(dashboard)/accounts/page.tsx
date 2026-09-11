import type { Metadata } from "next";
import { accountsApi } from "@/features/accounts/api";
import { AccountsView } from "@/features/accounts/AccountsView";
import type { CompanyModel, ContactModel } from "@/features/accounts/types";

export const metadata: Metadata = {
  title: "Accounts | Sales",
  description: "Manage accounts, client companies, and associated business contacts.",
};

export default async function AccountsPage() {
  let initialCompanies: CompanyModel[] = [];
  let initialContacts: ContactModel[] = [];

  try {
    const [compRes, contRes] = await Promise.allSettled([
      accountsApi.listCompanies({ skip: 0, limit: 100 }),
      accountsApi.listContacts({ skip: 0, limit: 100 }),
    ]);

    if (compRes.status === "fulfilled") {
      initialCompanies = compRes.value;
    }
    if (contRes.status === "fulfilled") {
      initialContacts = contRes.value;
    }
  } catch (error) {
    console.warn("Failed to prefetch accounts on server:", error);
  }

  return (
    <AccountsView
      initialCompanies={initialCompanies}
      initialContacts={initialContacts}
    />
  );
}
