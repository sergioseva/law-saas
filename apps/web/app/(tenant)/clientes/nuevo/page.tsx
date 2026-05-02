"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { ClientForm } from "../../../../components/client-form";
import { Card, CardBody, CardHeader, CardTitle } from "../../../../components/ui/card";
import { HttpError } from "../../../../lib/api/client";
import { useCreateClient } from "../../../../lib/hooks/use-clients";

export default function NewClientPage() {
  const router = useRouter();
  const create = useCreateClient();
  const [serverErrors, setServerErrors] = useState<Record<string, string>>({});

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Nuevo cliente</h1>

      <Card>
        <CardHeader>
          <CardTitle>Datos del cliente</CardTitle>
        </CardHeader>
        <CardBody>
          <ClientForm
            submitLabel="Crear"
            isSubmitting={create.isPending}
            serverErrors={serverErrors}
            onSubmit={(values) => {
              setServerErrors({});
              create.mutate(values, {
                onSuccess: (created) => {
                  router.push(`/clientes/${created.id}`);
                },
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
