"use client";

import { useEffect } from "react";

import { AuthGuard } from "../../components/auth-guard";
import { Header } from "../../components/header";
import { ensureCsrf } from "../../lib/api/client";

export default function TenantLayout({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    ensureCsrf().catch(() => undefined);
  }, []);

  return (
    <AuthGuard>
      <Header />
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </AuthGuard>
  );
}
