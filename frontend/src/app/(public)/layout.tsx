import type { ReactNode } from "react";

// Public routes share the root layout (fonts, AppProvider) with no auth guard.
// This layout is intentionally empty — just pass children through.
export default function PublicLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
