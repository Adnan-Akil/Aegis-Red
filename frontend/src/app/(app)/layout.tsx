import type { ReactNode } from "react";
import { AppShell } from "@/components/AppShell";
import { AuthWrapper } from "@/components/AuthWrapper";

// All protected routes are wrapped by AuthWrapper (session guard) and AppShell (nav/chrome).
// The h-screen overflow-hidden class pair is required for the dashboard layout to work correctly.
export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="h-screen w-screen overflow-hidden">
      <AuthWrapper>
        <AppShell>{children}</AppShell>
      </AuthWrapper>
    </div>
  );
}
