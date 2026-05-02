"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { FieldError } from "./ui/field-error";

const schema = z.object({
  description: z.string().min(1, "Requerido"),
  action_date: z.string().optional().default(""),
  next_action_date: z.string().optional().default(""),
  next_step: z.string().optional().default(""),
});

type FormValues = z.infer<typeof schema>;

export interface ActionFormProps {
  onSubmit: (values: {
    description: string;
    action_date: string | null;
    next_action_date: string | null;
    next_step: string;
  }) => void;
  isSubmitting?: boolean;
}

export function ActionForm({ onSubmit, isSubmitting }: ActionFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      description: "",
      action_date: new Date().toISOString().slice(0, 10),
      next_action_date: "",
      next_step: "",
    },
  });

  return (
    <form
      className="space-y-3"
      onSubmit={handleSubmit((values) => {
        onSubmit({
          description: values.description,
          action_date: values.action_date || null,
          next_action_date: values.next_action_date || null,
          next_step: values.next_step,
        });
        reset({
          description: "",
          action_date: new Date().toISOString().slice(0, 10),
          next_action_date: "",
          next_step: "",
        });
      })}
      noValidate
    >
      <div>
        <Label htmlFor="description">Descripción</Label>
        <Input id="description" {...register("description")} autoFocus />
        <FieldError message={errors.description?.message} />
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div>
          <Label htmlFor="action_date">Fecha</Label>
          <Input id="action_date" type="date" {...register("action_date")} />
        </div>
        <div>
          <Label htmlFor="next_action_date">Próxima fecha</Label>
          <Input id="next_action_date" type="date" {...register("next_action_date")} />
        </div>
        <div>
          <Label htmlFor="next_step">Próximo paso</Label>
          <Input id="next_step" {...register("next_step")} />
        </div>
      </div>

      <div className="flex justify-end">
        <Button type="submit" size="sm" disabled={isSubmitting}>
          {isSubmitting ? "Guardando…" : "Agregar"}
        </Button>
      </div>
    </form>
  );
}
