"use client";

import { useRouter } from "next/navigation";
import { type ReactNode, useEffect } from "react";

import { useMe } from "../lib/hooks/use-me";
import type { Role } from "../lib/api/types";

interface Props {
  children: ReactNode;
  /**
   * Minimum role required to access this subtree. If unset, only an active
   * session in this firm is required.
   */
  minRole?: "admin" | "abogado" | "secretario";
  loading?: ReactNode;
}

const LEVEL: Record<Role, number> = { admin: 30, abogado: 20, secretario: 10 };
const ROLE_LEVEL = { admin: 30, abogado: 20, secretario: 10 } as const;

export function AuthGuard({ children, minRole, loading }: Props) {
  const router = useRouter();
  const { data, isLoading, isError, error } = useMe();

  const status = (error as { status?: number } | undefined)?.status;
  const unauth = isError && (status === 401 || status === 403);

  useEffect(() => {
    if (unauth) router.replace("/login");
  }, [unauth, router]);

  if (isLoading) {
    return (
      loading ?? <div className="px-6 py-12 text-sm text-slate-500">Cargando…</div>
    );
  }

  if (unauth || !data) return null;
  if (!data.role || !data.firm) {
    // Logged in but no firm context (probably wrong subdomain).
    return (
      <div className="mx-auto max-w-md px-6 py-16 text-center text-slate-600">
        No tiene acceso a este estudio.
      </div>
    );
  }

  if (minRole && LEVEL[data.role] < ROLE_LEVEL[minRole]) {
    return (
      <div className="mx-auto max-w-md px-6 py-16 text-center text-slate-600">
        Permisos insuficientes para esta sección.
      </div>
    );
  }

  return <>{children}</>;
}
