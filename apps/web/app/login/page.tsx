"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { login, type LoginInput } from "../../lib/api/auth";
import { ensureCsrf, HttpError } from "../../lib/api/client";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Card, CardBody, CardHeader, CardTitle } from "../../components/ui/card";
import { FieldError } from "../../components/ui/field-error";
import { getCurrentSubdomain, getPublicSignupUrl } from "../../lib/env";

const schema = z.object({
  email: z.string().email("Email inválido"),
  password: z.string().min(1, "Requerido"),
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const qc = useQueryClient();
  const [serverError, setServerError] = useState<string | null>(null);
  const [subdomain, setSubdomain] = useState("");

  useEffect(() => {
    ensureCsrf().catch(() => undefined);
    setSubdomain(getCurrentSubdomain());
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  const mutation = useMutation({
    mutationFn: (input: LoginInput) => login(input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["me"] });
      router.push("/dashboard");
    },
    onError: (err: unknown) => {
      if (err instanceof HttpError) {
        if (err.status === 403) {
          setServerError("Este usuario no pertenece a este estudio.");
        } else if (err.status === 401) {
          setServerError("Email o contraseña incorrectos.");
        } else {
          setServerError(err.detail ?? `Error ${err.status}`);
        }
      } else {
        setServerError(err instanceof Error ? err.message : "Error inesperado");
      }
    },
  });

  function onSubmit(values: FormValues) {
    setServerError(null);
    mutation.mutate(values);
  }

  const isPublicHost = !subdomain || ["app", "www"].includes(subdomain);

  if (isPublicHost) {
    return (
      <main className="mx-auto max-w-md px-6 py-16 text-center">
        <h1 className="text-xl font-semibold">Ingresá en tu estudio</h1>
        <p className="mt-3 text-slate-600">
          Para iniciar sesión, abrí <span className="font-mono">tu-estudio.lawsaas.app</span>.
        </p>
        <p className="mt-6">
          <Link className="underline" href={getPublicSignupUrl()}>
            ¿No tienes estudio? Crear uno
          </Link>
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-md px-6 py-16">
      <Card>
        <CardHeader>
          <CardTitle>Ingresar — {subdomain}</CardTitle>
        </CardHeader>
        <CardBody>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                autoFocus
                {...register("email")}
              />
              <FieldError message={errors.email?.message} />
            </div>

            <div>
              <Label htmlFor="password">Contraseña</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                {...register("password")}
              />
              <FieldError message={errors.password?.message} />
            </div>

            {serverError ? <FieldError message={serverError} /> : null}

            <Button type="submit" className="w-full" disabled={mutation.isPending}>
              {mutation.isPending ? "Ingresando…" : "Ingresar"}
            </Button>
          </form>
        </CardBody>
      </Card>
    </main>
  );
}
