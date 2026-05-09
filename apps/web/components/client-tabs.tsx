"use client";

import { useRef, useState } from "react";

import { ActionForm } from "./action-form";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "./ui/card";
import { FieldError } from "./ui/field-error";
import { cn, formatDateAr, formatDateTimeAr } from "../lib/utils";
import type { ActionSummary, DocumentSummary, Role } from "../lib/api/types";
import {
  useActions,
  useCreateAction,
  useDeleteAction,
  useMarkActionCompleted,
} from "../lib/hooks/use-actions";
import {
  useDeleteDocument,
  useDocuments,
  useUploadDocument,
} from "../lib/hooks/use-documents";
import { downloadDocumentUrl } from "../lib/api/documents";
import { HttpError } from "../lib/api/client";

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
        <DocumentsPanel clientId={clientId} canWrite={canWrite} canDelete={canDelete} />
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
  canWrite,
  canDelete,
}: {
  clientId: number;
  canWrite: boolean;
  canDelete: boolean;
}) {
  const { data, isLoading } = useDocuments({ client: clientId });

  return (
    <div className="space-y-4">
      {canWrite ? <DocumentUploader clientId={clientId} /> : null}

      <Card>
        <CardHeader>
          <CardTitle>Documentos</CardTitle>
        </CardHeader>
        <CardBody className="p-0">
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
    </div>
  );
}

const ALLOWED_EXTS = ["pdf", "png", "jpg", "jpeg", "webp", "doc", "docx", "txt"];
const MAX_BYTES = 16 * 1024 * 1024;

function DocumentUploader({ clientId }: { clientId: number }) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const upload = useUploadDocument();

  function handleFiles(files: FileList | null | undefined) {
    if (!files || files.length === 0) return;
    const file = files[0];
    setError(null);

    const ext = file.name.toLowerCase().split(".").pop() ?? "";
    if (!ALLOWED_EXTS.includes(ext)) {
      setError(`Tipo de archivo .${ext} no permitido.`);
      return;
    }
    if (file.size > MAX_BYTES) {
      setError(`Archivo demasiado grande (máx. ${MAX_BYTES / (1024 * 1024)} MB).`);
      return;
    }

    setProgress(0);
    upload.mutate(
      {
        client: clientId,
        file,
        onProgress: (p) =>
          setProgress(p.total > 0 ? Math.round((p.loaded / p.total) * 100) : null),
      },
      {
        onSuccess: () => {
          setProgress(null);
          if (fileInputRef.current) fileInputRef.current.value = "";
        },
        onError: (err) => {
          setProgress(null);
          if (err instanceof HttpError && err.errors) {
            const flat = Object.entries(err.errors)
              .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(" ") : v}`)
              .join(" · ");
            setError(flat || err.detail || `Error ${err.status}`);
          } else {
            setError(err instanceof Error ? err.message : "Error en la carga");
          }
        },
      },
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Subir documento</CardTitle>
      </CardHeader>
      <CardBody>
        <label
          htmlFor={`upload-${clientId}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            handleFiles(e.dataTransfer.files);
          }}
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed px-6 py-10 text-center transition-colors",
            dragOver
              ? "border-slate-700 bg-slate-50"
              : "border-slate-300 hover:border-slate-400",
            upload.isPending && "pointer-events-none opacity-60",
          )}
        >
          <input
            ref={fileInputRef}
            id={`upload-${clientId}`}
            type="file"
            className="sr-only"
            accept={ALLOWED_EXTS.map((e) => `.${e}`).join(",")}
            disabled={upload.isPending}
            onChange={(e) => handleFiles(e.target.files)}
          />
          <p className="text-sm text-slate-700">
            {upload.isPending
              ? `Subiendo…${progress !== null ? ` ${progress}%` : ""}`
              : "Arrastrá un archivo o hacé clic para elegir uno"}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            PDF, imágenes, DOC, TXT — hasta {MAX_BYTES / (1024 * 1024)} MB
          </p>
        </label>

        {progress !== null ? (
          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-200">
            <div
              className="h-full bg-slate-900 transition-[width]"
              style={{ width: `${progress}%` }}
            />
          </div>
        ) : null}

        <FieldError message={error ?? undefined} />
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
  const remove = useDeleteDocument();

  function handleDelete() {
    if (!confirm("¿Eliminar este documento?")) return;
    remove.mutate(doc.id);
  }

  return (
    <li className="flex items-center justify-between px-5 py-3">
      <div className="min-w-0 flex-1">
        <a
          href={downloadDocumentUrl(doc.id)}
          target="_blank"
          rel="noopener noreferrer"
          className="block truncate text-sm font-medium text-slate-900 hover:underline"
        >
          {doc.stored_key.split("/").pop() ?? doc.stored_key}
        </a>
        <div className="text-xs text-slate-500">
          {doc.mime_type} · {formatBytes(doc.size_bytes)} · subido{" "}
          {formatDateTimeAr(doc.uploaded_at)}
        </div>
      </div>
      <div className="flex shrink-0 gap-1">
        <a
          href={downloadDocumentUrl(doc.id)}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex h-8 items-center rounded-md px-3 text-sm text-slate-700 hover:bg-slate-100"
        >
          Descargar
        </a>
        {canDelete ? (
          <Button
            size="sm"
            variant="ghost"
            onClick={handleDelete}
            disabled={remove.isPending}
          >
            Eliminar
          </Button>
        ) : null}
      </div>
    </li>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
