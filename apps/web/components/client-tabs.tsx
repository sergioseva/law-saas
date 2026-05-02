"use client";

import { useState } from "react";

import { ActionForm } from "./action-form";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "./ui/card";
import { cn, formatDateAr, formatDateTimeAr } from "../lib/utils";
import type { ActionSummary, DocumentSummary, Role } from "../lib/api/types";
import {
  useActions,
  useCreateAction,
  useDeleteAction,
  useMarkActionCompleted,
} from "../lib/hooks/use-actions";
import { useDocuments } from "../lib/hooks/use-documents";

type Tab = "actions" | "documents";

export function ClientTabs({ clientId, role }: { clientId: number; role: Role | null }) {
  const [tab, setTab] = useState<Tab>("actions");
  const canWrite = role === "admin" || role === "abogado";
  const canDelete = role === "admin";

  return (
    <div className="space-y-4">
      <div className="flex gap-1 border-b border-slate-200">
        <TabButton active={tab === "actions"} onClick={() => setTab("actions")}>
          Actuaciones
        </TabButton>
        <TabButton active={tab === "documents"} onClick={() => setTab("documents")}>
          Documentos
        </TabButton>
      </div>

      {tab === "actions" ? (
        <ActionsPanel clientId={clientId} canWrite={canWrite} canDelete={canDelete} />
      ) : (
        <DocumentsPanel clientId={clientId} canDelete={canDelete} />
      )}
    </div>
  );
}

function TabButton({
  active,
  ...rest
}: {
  active: boolean;
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      className={cn(
        "-mb-px border-b-2 px-4 py-2 text-sm font-medium",
        active
          ? "border-slate-900 text-slate-900"
          : "border-transparent text-slate-500 hover:text-slate-700",
      )}
      {...rest}
    />
  );
}

function ActionsPanel({
  clientId,
  canWrite,
  canDelete,
}: {
  clientId: number;
  canWrite: boolean;
  canDelete: boolean;
}) {
  const { data, isLoading } = useActions({ client: clientId });
  const create = useCreateAction(clientId);
  const complete = useMarkActionCompleted();
  const remove = useDeleteAction();

  return (
    <div className="space-y-4">
      {canWrite ? (
        <Card>
          <CardHeader>
            <CardTitle>Nueva actuación</CardTitle>
          </CardHeader>
          <CardBody>
            <ActionForm
              isSubmitting={create.isPending}
              onSubmit={(values) => create.mutate(values)}
            />
          </CardBody>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Historial</CardTitle>
        </CardHeader>
        <CardBody className="p-0">
          {isLoading ? (
            <p className="px-5 py-6 text-sm text-slate-500">Cargando…</p>
          ) : data && data.results.length > 0 ? (
            <ul className="divide-y divide-slate-200">
              {data.results.map((a) => (
                <ActionRow
                  key={a.id}
                  action={a}
                  canWrite={canWrite}
                  canDelete={canDelete}
                  onComplete={() => complete.mutate(a.id)}
                  onDelete={() => remove.mutate(a.id)}
                />
              ))}
            </ul>
          ) : (
            <p className="px-5 py-12 text-center text-sm text-slate-500">
              Sin actuaciones todavía.
            </p>
          )}
        </CardBody>
      </Card>
    </div>
  );
}

function ActionRow({
  action,
  canWrite,
  canDelete,
  onComplete,
  onDelete,
}: {
  action: ActionSummary;
  canWrite: boolean;
  canDelete: boolean;
  onComplete: () => void;
  onDelete: () => void;
}) {
  return (
    <li className="flex items-start justify-between gap-4 px-5 py-3">
      <div>
        <div className="text-sm text-slate-900">
          {action.next_step ?? "(sin descripción)"}
        </div>
        <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
          <span>Fecha: {formatDateAr(action.action_date)}</span>
          {action.next_action_date ? (
            <span>· Próx.: {formatDateAr(action.next_action_date)}</span>
          ) : null}
          {action.completed ? (
            <Badge tone="success">Hecho</Badge>
          ) : (
            <Badge tone="info">Pendiente</Badge>
          )}
        </div>
      </div>
      <div className="flex shrink-0 gap-1">
        {canWrite && !action.completed ? (
          <Button size="sm" variant="ghost" onClick={onComplete}>
            Marcar hecho
          </Button>
        ) : null}
        {canDelete ? (
          <Button size="sm" variant="ghost" onClick={onDelete}>
            Eliminar
          </Button>
        ) : null}
      </div>
    </li>
  );
}

function DocumentsPanel({
  clientId,
  canDelete,
}: {
  clientId: number;
  canDelete: boolean;
}) {
  const { data, isLoading } = useDocuments({ client: clientId });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Documentos</CardTitle>
      </CardHeader>
      <CardBody className="p-0">
        <p className="border-b border-slate-200 bg-amber-50 px-5 py-2 text-xs text-amber-800">
          La carga de documentos se habilita en Phase 4 (R2 + URLs firmadas).
        </p>
        {isLoading ? (
          <p className="px-5 py-6 text-sm text-slate-500">Cargando…</p>
        ) : data && data.results.length > 0 ? (
          <ul className="divide-y divide-slate-200">
            {data.results.map((doc) => (
              <DocumentRow key={doc.id} doc={doc} canDelete={canDelete} />
            ))}
          </ul>
        ) : (
          <p className="px-5 py-12 text-center text-sm text-slate-500">
            Sin documentos.
          </p>
        )}
      </CardBody>
    </Card>
  );
}

function DocumentRow({
  doc,
  canDelete,
}: {
  doc: DocumentSummary;
  canDelete: boolean;
}) {
  return (
    <li className="flex items-center justify-between px-5 py-3">
      <div>
        <div className="text-sm text-slate-900">{doc.stored_key}</div>
        <div className="text-xs text-slate-500">
          {doc.mime_type} · {formatBytes(doc.size_bytes)} · subido{" "}
          {formatDateTimeAr(doc.uploaded_at)}
        </div>
      </div>
      {canDelete ? (
        <Button size="sm" variant="ghost" disabled>
          Eliminar
        </Button>
      ) : null}
    </li>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
