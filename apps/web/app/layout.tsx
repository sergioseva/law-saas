import type { Metadata } from "next";
import type { ReactNode } from "react";

import { QueryProvider } from "../lib/providers/query-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "law-saas",
  description: "Gestión de estudios jurídicos",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
