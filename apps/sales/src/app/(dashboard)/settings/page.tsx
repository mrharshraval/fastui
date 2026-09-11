import { Suspense } from "react";
import { settingsApi } from "@/features/settings/api";
import { SettingsView } from "@/features/settings/SettingsView";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  let initialUser = null;
  try {
    initialUser = await settingsApi.getCurrentUser();
  } catch (err) {
    console.error("[SettingsPage] SSR prefetch failed:", err);
  }

  return (
    <Suspense fallback={null}>
      <SettingsView initialUser={initialUser as any} />
    </Suspense>
  );
}
