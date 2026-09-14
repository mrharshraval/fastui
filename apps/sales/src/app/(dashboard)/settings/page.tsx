import { Suspense } from "react";
import { SettingsView } from "@/features/settings/SettingsView";

export const dynamic = "force-dynamic";

/**
 * Settings Page.
 * Consumes the authoritative session already resolved by DashboardLayout and
 * distributed by SessionProvider without initiating redundant backend queries.
 */
export default function SettingsPage() {
  return (
    <Suspense fallback={null}>
      <SettingsView />
    </Suspense>
  );
}
