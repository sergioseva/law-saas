"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { ClientForm } from "../../../../../components/client-form";
import { Card, CardBody, CardHeader, CardTitle } from "../../../../../components/ui/card";
import { HttpError } from "../../../../../lib/api/client";
import { useClient, useUpdateClient } from "../../../../../lib/hooks/use-clients";

export default function EditClientPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const router = useRouter();
  const { data, isLoading } = useClient(id);
  const update = useUpdateClient(id);
  const [serverErrors, setServerErrors] = useState<Record<string, string>>({});

  if (isLoading) {
    return <p className="text-sm text-slate-500">Cargando…</p>;
  }
  if (!data) return null;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">
        Editar — {data.full_name ?? `Cliente #${data.id}`}
      </h1>

      <Card>
        <CardHeader>
          <CardTitle>Datos del cliente</CardTitle>
        </CardHeader>
        <CardBody>
          <ClientForm
            initial={data}
            submitLabel="Guardar"
            isSubmitting={update.isPending}
            serverErrors={serverErrors}
            onSubmit={(values) => {
              setServerErrors({});
              update.mutate(values, {
                onSuccess: () => router.push(`/clientes/${id}`),
                onError: (err) => {
                  if (err instanceof HttpError && err.errors) {
                    const flat: Record<string, string> = {};
                    for (const [k, v] of Object.entries(err.errors)) {
                      flat[k] = Array.isArray(v) ? v.join(" ") : String(v);
                    }
                    setServerErrors(flat);
                  } else {
                    setServerErrors({ _: err instanceof Error ? err.message : "Error" });
                  }
                },
              });
            }}
          />
        </CardBody>
      </Card>
    </div>
  );
}
