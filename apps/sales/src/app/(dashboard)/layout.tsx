import * as React from "react";
import { requireSession } from "@/core/auth/server-session";
import { SessionProvider } from "@/providers/session-provider";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { MobileBottomNav } from "@/components/mobile-bottom-nav";

/**
 * Server Component dashboard layout.
 * Authoritatively resolves the authenticated session server-side before rendering.
 * Passes the server-resolved session to SessionProvider for distribution to
 * interactive client leaves.
 */
export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await requireSession();

  return (
    <SessionProvider session={session}>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset className="bg-background flex flex-col flex-1 min-w-0">
          {/* Main content area with bottom clearance for mobile nav */}
          <div className="flex flex-1 flex-col pb-20 md:pb-0">
            {children}
          </div>
        </SidebarInset>
        <MobileBottomNav />
      </SidebarProvider>
    </SessionProvider>
  );
}
