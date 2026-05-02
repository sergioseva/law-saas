"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";

import { logout } from "../lib/api/auth";
import { useMe } from "../lib/hooks/use-me";
import { Button } from "./ui/button";
import { cn } from "../lib/utils";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/clientes", label: "Clientes" },
];

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const qc = useQueryClient();
  const { data } = useMe();

  if (!data?.firm) return null;

  async function handleLogout() {
    await logout();
    qc.removeQueries();
    router.push("/login");
  }

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <div className="flex items-center gap-6">
          <span className="text-sm font-semibold text-slate-900">
            {data.firm.name}
          </span>
          <nav className="flex items-center gap-1">
            {NAV.map((item) => {
              const active = pathname === item.href || pathname.startsWith(item.href + "/");
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "rounded-md px-3 py-1.5 text-sm",
                    active
                      ? "bg-slate-900 text-white"
                      : "text-slate-700 hover:bg-slate-100",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-3 text-sm text-slate-600">
          <span>
            {data.email} <span className="text-slate-400">·</span> {data.role}
          </span>
          <Button size="sm" variant="ghost" onClick={handleLogout}>
            Salir
          </Button>
        </div>
      </div>
    </header>
  );
}
