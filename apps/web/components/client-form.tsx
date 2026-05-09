"use client";

import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "./ui/button";
import { DateInputAr } from "./ui/date-input-ar";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select } from "./ui/select";
import { FieldError } from "./ui/field-error";
import type { ClientDetail, ClientWriteInput } from "../lib/api/types";

const STATUSES = ["consulta", "en proceso", "demanda iniciada", "cerrado"] as const;
const TYPES = ["Extrajudicial", "Judicial"] as const;
const LABELS = ["", "+10", "-10"] as const;

const schema = z.object({
  full_name: z.string().min(1, "Requerido"),
  dni_cuil: z.string().optional().default(""),
  birth_date: z.string().optional().default(""),
  phone: z.string().optional().default(""),
  email: z
    .string()
    .optional()
    .default("")
    .refine((v) => !v || /^\S+@\S+\.\S+$/.test(v), "Email inválido"),
  address: z.string().optional().default(""),
  city: z.string().optional().default(""),
  employer: z.string().optional().default(""),
  insurer: z.string().optional().default(""),
  case_reason: z.string().optional().default(""),
  case_status: z.enum(STATUSES).default("consulta"),
  case_type: z.enum(TYPES).default("Extrajudicial"),
  case_label: z.enum(LABELS).default(""),
  first_visit_date: z.string().optional().default(""),
});

type FormValues = z.infer<typeof schema>;

export interface ClientFormProps {
  initial?: ClientDetail;
  submitLabel: string;
  onSubmit: (values: ClientWriteInput) => void;
  isSubmitting?: boolean;
  serverErrors?: Record<string, string>;
}

export function ClientForm({
  initial,
  submitLabel,
  onSubmit,
  isSubmitting,
  serverErrors = {},
}: ClientFormProps) {
  const {
    register,
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      full_name: initial?.full_name ?? "",
      dni_cuil: initial?.dni_cuil ?? "",
      birth_date: initial?.birth_date ?? "",
      phone: initial?.phone ?? "",
      email: initial?.email ?? "",
      address: initial?.address ?? "",
      city: initial?.city ?? "",
      employer: initial?.employer ?? "",
      insurer: initial?.insurer ?? "",
      case_reason: initial?.case_reason ?? "",
      case_status: (initial?.case_status as (typeof STATUSES)[number]) ?? "consulta",
      case_type: (initial?.case_type as (typeof TYPES)[number]) ?? "Extrajudicial",
      case_label: (initial?.case_label as (typeof LABELS)[number]) ?? "",
      first_visit_date: initial?.first_visit_date ?? "",
    },
  });

  function submit(values: FormValues) {
    const cleaned: ClientWriteInput = {
      full_name: values.full_name,
      dni_cuil: values.dni_cuil || undefined,
      birth_date: values.birth_date || null,
      phone: values.phone || undefined,
      email: values.email || undefined,
      address: values.address || undefined,
      city: values.city || undefined,
      employer: values.employer || undefined,
      insurer: values.insurer || undefined,
      case_reason: values.case_reason || undefined,
      case_status: values.case_status,
      case_type: values.case_type,
      case_label: values.case_label,
      first_visit_date: values.first_visit_date || null,
    };
    onSubmit(cleaned);
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit(submit)} noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Label htmlFor="full_name">Nombre completo *</Label>
          <Input id="full_name" {...register("full_name")} />
          <FieldError message={errors.full_name?.message ?? serverErrors.full_name} />
        </div>

        <div>
          <Label htmlFor="dni_cuil">DNI / CUIL</Label>
          <Input id="dni_cuil" {...register("dni_cuil")} />
          <FieldError message={errors.dni_cuil?.message ?? serverErrors.dni_cuil} />
        </div>

        <div>
          <Label htmlFor="birth_date">Fecha de nacimiento</Label>
          <Controller
            name="birth_date"
            control={control}
            render={({ field }) => (
              <DateInputAr
                id="birth_date"
                value={field.value}
                onChange={field.onChange}
                onBlur={field.onBlur}
              />
            )}
          />
        </div>

        <div>
          <Label htmlFor="phone">Teléfono</Label>
          <Input id="phone" {...register("phone")} />
        </div>

        <div>
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" {...register("email")} />
          <FieldError message={errors.email?.message ?? serverErrors.email} />
        </div>

        <div className="sm:col-span-2">
          <Label htmlFor="address">Dirección</Label>
          <Input id="address" {...register("address")} />
        </div>

        <div>
          <Label htmlFor="city">Ciudad</Label>
          <Input id="city" {...register("city")} />
        </div>

        <div>
          <Label htmlFor="first_visit_date">Primera visita</Label>
          <Controller
            name="first_visit_date"
            control={control}
            render={({ field }) => (
              <DateInputAr
                id="first_visit_date"
                value={field.value}
                onChange={field.onChange}
                onBlur={field.onBlur}
              />
            )}
          />
        </div>

        <div>
          <Label htmlFor="employer">Empleador</Label>
          <Input id="employer" {...register("employer")} />
        </div>

        <div>
          <Label htmlFor="insurer">ART</Label>
          <Input id="insurer" {...register("insurer")} />
        </div>

        <div>
          <Label htmlFor="case_status">Estado</Label>
          <Select id="case_status" {...register("case_status")}>
            {STATUSES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </Select>
        </div>

        <div>
          <Label htmlFor="case_type">Tipo</Label>
          <Select id="case_type" {...register("case_type")}>
            {TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </Select>
        </div>

        <div>
          <Label htmlFor="case_label">Etiqueta</Label>
          <Select id="case_label" {...register("case_label")}>
            {LABELS.map((l) => (
              <option key={l} value={l}>{l ? l : "—"}</option>
            ))}
          </Select>
        </div>

        <div className="sm:col-span-2">
          <Label htmlFor="case_reason">Motivo del caso</Label>
          <textarea
            id="case_reason"
            {...register("case_reason")}
            rows={3}
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-700"
          />
        </div>
      </div>

      {serverErrors._ ? <FieldError message={serverErrors._} /> : null}

      <div className="flex justify-end">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Guardando…" : submitLabel}
        </Button>
      </div>
    </form>
  );
}
