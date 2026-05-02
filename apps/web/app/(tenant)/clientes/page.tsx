"use client";

import Link from "next/link";
import { useState } from "react";

import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { Card, CardBody } from "../../../components/ui/card";
import { Input } from "../../../components/ui/input";
import { Select } from "../../../components/ui/select";
import { useClients } from "../../../lib/hooks/use-clients";
import { useMe } from "../../../lib/hooks/use-me";
import { formatDateAr } from "../../../lib/utils";

const STATUSES = ["", "consulta", "en proceso", "demanda iniciada", "cerrado"] as const;

const statusTone: Record<string, "neutral" | "info" | "warning" | "success" | "danger"> = {
  consulta: "info",
  "en proceso": "warning",
  "demanda iniciada": "danger",
  cerrado: "neutral",
};

export default function ClientesPage() {
  const { data: me } = useMe();
  const canWrite = me?.role === "admin" || me?.role === "abogado";

  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");

  const params: { q?: string; case_status?: string } = {};
  if (q) params.q = q;
  if (status) params.case_status = status;

  const { data, isLoading } = useClients(params);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Clientes</h1>
        {canWrite ? (
          <Link href="/clientes/nuevo">
            <Button>Nuevo cliente</Button>
          </Link>
        ) : null}
      </div>

      <div className="flex flex-wrap gap-3">
        <Input
          placeholder="Buscar por nombre, DNI o teléfono…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="max-w-sm"
        />
        <Select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="max-w-xs"
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s ? s : "Todos los estados"}
            </option>
          ))}
        </Select>
      </div>

      <Card>
        <CardBody className="p-0">
          {isLoading ? (
            <p className="px-5 py-6 text-sm text-slate-500">Cargando…</p>
          ) : data && data.results.length > 0 ? (
            <ul className="divide-y divide-slate-200">
              {data.results.map((c) => (
                <li key={c.id}>
                  <Link
                    href={`/clientes/${c.id}`}
                    className="flex items-center justify-between px-5 py-3 hover:bg-slate-50"
                  >
                    <div>
                      <div className="font-medium text-slate-900">
                        {c.full_name_display ?? `Cliente #${c.id}`}
                      </div>
                      <div className="text-xs text-slate-500">
                        {c.city_display ?? "—"} · primera visita{" "}
                        {formatDateAr(c.first_visit_date)}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge tone={statusTone[c.case_status] ?? "neutral"}>
                        {c.case_status}
                      </Badge>
                      <Badge tone="neutral">{c.case_type}</Badge>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="px-5 py-12 text-center text-sm text-slate-500">
              No hay clientes que coincidan.
            </p>
          )}
        </CardBody>
      </Card>

      {data && data.count > 0 ? (
        <p className="text-xs text-slate-500">
          Mostrando {data.results.length} de {data.count}
        </p>
      ) : null}
    </div>
  );
}
