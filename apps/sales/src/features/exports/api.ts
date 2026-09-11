import { client } from "@/core/api/client";
import type {
  ExportCreateRequest,
  ExportCreateResponse,
  ExportStatusResponse,
  ExportType,
  ExportScope,
} from "@/core/api/generated";

export type { ExportCreateRequest, ExportCreateResponse, ExportStatusResponse, ExportType, ExportScope };

export interface ExportFilterParams {
  search?: string;
  qualification_status?: string;
  stage?: string;
  signal?: string;
  priority?: string;
  website?: string;
  source?: string;
  sort_by?: string;
  sort_order?: string;
}

const API_BASE =
  typeof window !== "undefined"
    ? "/api/proxy/v1"
    : `${(process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "")}/v1`;

/**
 * Downloads a file blob from the API and triggers native browser download.
 */
export async function downloadFileBlob(
  path: string,
  fallbackFilename: string,
  signal?: AbortSignal
): Promise<void> {
  let cleanPath = path.startsWith("/") ? path : `/${path}`;
  if (cleanPath.startsWith("/v1/")) {
    cleanPath = cleanPath.slice(3); // Remove leading /v1 so we don't get /v1/v1/
  }
  const url = `${API_BASE}${cleanPath}`;

  const res = await fetch(url, {
    method: "GET",
    credentials: "include",
    cache: "no-store",
    signal,
  });

  if (!res.ok) {
    let errorMessage = `Download failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson?.detail) {
        errorMessage = errJson.detail;
      }
    } catch {
      // Body not JSON
    }
    throw new Error(errorMessage);
  }

  let filename = fallbackFilename;
  const disposition = res.headers.get("Content-Disposition");
  if (disposition) {
    const match = /filename\*?=['"]?(?:UTF-\d['"]*)?([^;\r\n"']*)['"]?/i.exec(disposition);
    if (match && match[1]) {
      filename = decodeURIComponent(match[1].trim());
    }
  }

  const blob = await res.blob();
  const blobUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = blobUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);

  setTimeout(() => {
    window.URL.revokeObjectURL(blobUrl);
  }, 1000);
}

export interface RunExportOptions {
  request: ExportCreateRequest;
  onProgress?: (status: ExportStatusResponse) => void;
  signal?: AbortSignal;
}

/**
 * Initiates an export job, polls with immutable exportId scoping to guarantee
 * `/exports/undefined` can NEVER occur, and triggers file download.
 */
export async function runExportAndDownload({
  request,
  onProgress,
  signal,
}: RunExportOptions): Promise<void> {
  // 1. Initiate export job: POST /v1/exports
  const initRes = await client.post<ExportCreateResponse>("/v1/exports", request);
  if (!initRes || !initRes.export_id) {
    throw new Error("Failed to initiate export job.");
  }

  // Immutable identifier scoping: protects against schema divergence between POST and GET
  const exportId = initRes.export_id;

  const pollIntervalMs = 500;
  const maxPolls = 600; // 5 minutes timeout

  let latestStatus: ExportStatusResponse | null = null;

  for (let pollCount = 0; pollCount < maxPolls; pollCount++) {
    if (signal?.aborted) {
      throw new DOMException("Export was cancelled.", "AbortError");
    }

    // 2. Poll: GET /v1/exports/{id}
    const statusRes = await client.get<ExportStatusResponse>(`/v1/exports/${exportId}`);
    latestStatus = statusRes;
    onProgress?.(statusRes);

    if (statusRes.status === "completed") {
      break;
    }

    if (statusRes.status === "failed") {
      throw new Error(statusRes.error_message || "Export processing failed.");
    }

    await new Promise((resolve, reject) => {
      const timer = setTimeout(resolve, pollIntervalMs);
      if (signal) {
        signal.addEventListener(
          "abort",
          () => {
            clearTimeout(timer);
            reject(new DOMException("Export was cancelled.", "AbortError"));
          },
          { once: true }
        );
      }
    });
  }

  if (!latestStatus || latestStatus.status !== "completed") {
    throw new Error("Export timed out. Please try a narrower filter.");
  }

  // 3. Download: GET /v1/exports/{id}/download
  const downloadPath = latestStatus.download_url || `/v1/exports/${exportId}/download`;
  const dateStr = new Date().toISOString().slice(0, 10);
  const defaultFilename = `${request.export_type}_export_${dateStr}.csv`;

  await downloadFileBlob(downloadPath, defaultFilename, signal);
}
