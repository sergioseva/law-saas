"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";

import {
  type ExportFormat,
  exportDownloadUrl,
  getExportStatus,
  startExport,
} from "../api/exports";

type Phase = "idle" | "queued" | "ready" | "failed";

export interface ExportState {
  phase: Phase;
  taskId: string | null;
  downloadUrl: string | null;
  error: string | null;
}

/**
 * Kick off an export and poll for its result. Returns a stable handle the
 * caller can wire to a button.
 */
export function useExport() {
  const [state, setState] = useState<ExportState>({
    phase: "idle",
    taskId: null,
    downloadUrl: null,
    error: null,
  });

  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (pollTimer.current) clearTimeout(pollTimer.current);
    };
  }, []);

  const enqueue = useMutation({
    mutationFn: (format: ExportFormat) => startExport(format),
    onSuccess: (data) => {
      setState({ phase: "queued", taskId: data.task_id, downloadUrl: null, error: null });
      poll(data.task_id);
    },
    onError: (err) => {
      setState({
        phase: "failed",
        taskId: null,
        downloadUrl: null,
        error: err instanceof Error ? err.message : "Error",
      });
    },
  });

  function poll(taskId: string) {
    if (pollTimer.current) clearTimeout(pollTimer.current);
    pollTimer.current = setTimeout(async () => {
      try {
        const result = await getExportStatus(taskId);
        if (result.status === "ready") {
          setState({
            phase: "ready",
            taskId,
            downloadUrl: exportDownloadUrl(taskId),
            error: null,
          });
        } else if (result.status === "failed") {
          setState({
            phase: "failed",
            taskId,
            downloadUrl: null,
            error: "El export falló.",
          });
        } else {
          poll(taskId);
        }
      } catch (err) {
        setState({
          phase: "failed",
          taskId,
          downloadUrl: null,
          error: err instanceof Error ? err.message : "Error",
        });
      }
    }, 1500);
  }

  function reset() {
    if (pollTimer.current) clearTimeout(pollTimer.current);
    setState({ phase: "idle", taskId: null, downloadUrl: null, error: null });
  }

  return {
    ...state,
    isPending: enqueue.isPending || state.phase === "queued",
    start: (format: ExportFormat) => enqueue.mutate(format),
    reset,
  };
}
