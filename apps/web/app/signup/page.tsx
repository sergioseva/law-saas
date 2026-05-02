"use client";

import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { signup, type SignupInput } from "../../lib/api/auth";
import { ensureCsrf, HttpError } from "../../lib/api/client";
import { getFirmUrl } from "../../lib/env";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Card, CardBody, CardHeader, CardTitle } from "../../components/ui/card";
import { FieldError } from "../../components/ui/field-error";

const schema = z.object({
  firm_name: z.string().min(1, "Requerido").max(200),
  subdomain: z
    .string()
    .min(3, "Mínimo 3 caracteres")
    .max(63)
    .regex(/^[a-z0-9](?:[a-z0-9-]{1,61}[a-z0-9])?$/, "Solo minúsculas, dígitos y guiones"),
  email: z.string().email("Email inválido"),
  password: z.string().min(12, "Mínimo 12 caracteres"),
});

type FormValues = z.infer<typeof schema>;

export default function SignupPage() {
  const [serverErrors, setServerErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    ensureCsrf().catch(() => undefined);
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { firm_name: "", subdomain: "", email: "", password: "" },
  });

  const mutation = useMutation({
    mutationFn: (input: SignupInput) => signup(input),
    onSuccess: (data) => {
      // Backend's redirect_url doesn't know about the dev-server port.
      // Construct the URL on the frontend from window.location + subdomain.
      window.location.href = getFirmUrl(data.firm.subdomain) + "/login";
    },
    onError: (err: unknown) => {
      if (err instanceof HttpError && err.errors) {
        const flat: Record<string, string> = {};
        for (const [k, v] of Object.entries(err.errors)) {
          flat[k] = Array.isArray(v) ? v.join(" ") : String(v);
        }
        setServerErrors(flat);
      } else {
        setServerErrors({ _: err instanceof Error ? err.message : "Error inesperado" });
      }
    },
  });

  function onSubmit(values: FormValues) {
    setServerErrors({});
    mutation.mutate(values);
  }

  return (
    <main className="mx-auto max-w-md px-6 py-16">
      <Card>
        <CardHeader>
          <CardTitle>Crear estudio</CardTitle>
        </CardHeader>
        <CardBody>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
            <div>
              <Label htmlFor="firm_name">Nombre del estudio</Label>
              <Input id="firm_name" {...register("firm_name")} autoFocus />
              <FieldError message={errors.firm_name?.message ?? serverErrors.firm_name} />
            </div>

            <div>
              <Label htmlFor="subdomain">Subdominio</Label>
              <div className="mt-1 flex items-center gap-2">
                <Input
                  id="subdomain"
                  {...register("subdomain")}
                  placeholder="tu-estudio"
                  className="lowercase"
                />
                <span className="text-sm text-slate-500">.lawsaas.app</span>
              </div>
              <FieldError message={errors.subdomain?.message ?? serverErrors.subdomain} />
            </div>

            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" autoComplete="email" {...register("email")} />
              <FieldError message={errors.email?.message ?? serverErrors.email} />
            </div>

            <div>
              <Label htmlFor="password">Contraseña</Label>
              <Input
                id="password"
                type="password"
                autoComplete="new-password"
                {...register("password")}
              />
              <FieldError message={errors.password?.message ?? serverErrors.password} />
            </div>

            {serverErrors._ ? (
              <FieldError message={serverErrors._} />
            ) : null}

            <Button type="submit" className="w-full" disabled={mutation.isPending}>
              {mutation.isPending ? "Creando…" : "Crear estudio"}
            </Button>
          </form>
        </CardBody>
      </Card>

      <p className="mt-6 text-center text-sm text-slate-600">
        ¿Ya tienes cuenta? <Link href="/" className="underline">Volver al inicio</Link>.
      </p>
    </main>
  );
}
