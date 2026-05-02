"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { ClientTabs } from "../../../../components/client-tabs";
import { Badge } from "../../../../components/ui/badge";
import { Button } from "../../../../components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "../../../../components/ui/card";
import { useClient, useDeleteClient } from "../../../../lib/hooks/use-clients";
import { useMe } from "../../../../lib/hooks/use-me";
import { formatDateAr } from "../../../../lib/utils";

export default function ClientDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const router = useRouter();
  const { data, isLoading, isError } = useClient(id);
  const remove = useDeleteClient();
  const { data: me } = useMe();
  const canWrite = me?.role === "admin" || me?.role === "abogado";
  const canDelete = me?.role === "admin";

  if (isLoading) {
    return <p className="text-sm text-slate-500">Cargando…</p>;
  }
  if (isError || !data) {
    return (
      <div className="text-center">
        <p className="text-slate-600">Cliente no encontrado.</p>
        <Link href="/clientes" className="mt-3 inline-block text-sm underline">
          Volver
        </Link>
      </div>
    );
  }

  function handleDelete() {
    if (!confirm("¿Eliminar este cliente y toda su información asociada?")) return;
    remove.mutate(id, {
      onSuccess: () => router.push("/clientes"),
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link href="/clientes" className="text-xs text-slate-500 hover:underline">
            ← Clientes
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">
            {data.full_name ?? `Cliente #${data.id}`}
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Badge tone="info">{data.case_status}</Badge>
            <Badge tone="neutral">{data.case_type}</Badge>
            {data.case_label ? <Badge tone="warning">{data.case_label}</Badge> : null}
            {data.first_visit_date ? (
              <span className="text-xs text-slate-500">
                Primera visita {formatDateAr(data.first_visit_date)}
              </span>
            ) : null}
          </div>
        </div>
        <div className="flex gap-2">
          {canWrite ? (
            <Link href={`/clientes/${id}/editar`}>
              <Button variant="secondary">Editar</Button>
            </Link>
          ) : null}
          {canDelete ? (
            <Button variant="danger" onClick={handleDelete}>
              Eliminar
            </Button>
          ) : null}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Información</CardTitle>
        </CardHeader>
        <CardBody>
          <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
            <Field label="DNI / CUIL" value={data.dni_cuil} />
            <Field label="Nacimiento" value={formatDateAr(data.birth_date)} />
            <Field label="Teléfono" value={data.phone} />
            <Field label="Email" value={data.email} />
            <Field label="Ciudad" value={data.city ?? undefined} />
            <Field label="Dirección" value={data.address} />
            <Field label="Empleador" value={data.employer} />
            <Field label="ART" value={data.insurer} />
            {data.case_reason ? (
              <div className="sm:col-span-2">
                <dt className="text-xs uppercase tracking-wide text-slate-500">
                  Motivo
                </dt>
                <dd className="text-sm text-slate-800">{data.case_reason}</dd>
              </div>
            ) : null}
          </dl>
        </CardBody>
      </Card>

      <ClientTabs clientId={id} role={me?.role ?? null} />
    </div>
  );
}

function Field({ label, value }: { label: string; value: string | undefined }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="text-sm text-slate-800">{value && value.trim() ? value : "—"}</dd>
    </div>
  );
}
