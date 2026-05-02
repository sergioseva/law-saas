"use client";

import Link from "next/link";

import { listActions } from "../../../lib/api/actions";
import { listClients } from "../../../lib/api/clients";
import { useQuery } from "@tanstack/react-query";
import { Card, CardBody, CardHeader, CardTitle } from "../../../components/ui/card";
import { Badge } from "../../../components/ui/badge";
import { formatDateAr } from "../../../lib/utils";
import { useMe } from "../../../lib/hooks/use-me";

export default function DashboardPage() {
  const { data: me } = useMe();
  const totalClients = useQuery({
    queryKey: ["clients", { page: 1 }],
    queryFn: () => listClients({ page: 1 }),
  });
  const activeCases = useQuery({
    queryKey: ["clients", { case_status: "en proceso" }],
    queryFn: () => listClients({ case_status: "en proceso" }),
  });
  const upcoming = useQuery({
    queryKey: ["actions", { completed: false }],
    queryFn: () => listActions({ completed: false }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-600">Bienvenido, {me?.email}.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardBody>
            <div className="text-sm text-slate-500">Total clientes</div>
            <div className="mt-2 text-3xl font-semibold text-slate-900">
              {totalClients.data?.count ?? "—"}
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <div className="text-sm text-slate-500">Casos en proceso</div>
            <div className="mt-2 text-3xl font-semibold text-slate-900">
              {activeCases.data?.count ?? "—"}
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <div className="text-sm text-slate-500">Actuaciones pendientes</div>
            <div className="mt-2 text-3xl font-semibold text-slate-900">
              {upcoming.data?.count ?? "—"}
            </div>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Próximas actuaciones</CardTitle>
        </CardHeader>
        <CardBody>
          {upcoming.isLoading ? (
            <p className="text-sm text-slate-500">Cargando…</p>
          ) : upcoming.data && upcoming.data.results.length > 0 ? (
            <ul className="divide-y divide-slate-200">
              {upcoming.data.results.slice(0, 8).map((a) => (
                <li key={a.id} className="flex items-center justify-between py-2">
                  <Link
                    href={`/clientes/${a.client}`}
                    className="text-sm text-slate-700 hover:underline"
                  >
                    {a.next_step ?? "(sin descripción)"}
                  </Link>
                  <div className="flex items-center gap-3 text-xs text-slate-500">
                    <span>{formatDateAr(a.next_action_date)}</span>
                    {a.completed ? (
                      <Badge tone="success">Hecho</Badge>
                    ) : (
                      <Badge tone="info">Pendiente</Badge>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">Sin actuaciones pendientes.</p>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
