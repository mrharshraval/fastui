import { api } from "@/lib/api"

export type ExportType = "prospects" | "leads" | "businesses"
export type ExportScope = "selected" | "filtered"

export interface ExportFilterParams {
  search?: string
  qualification_status?: string
  stage?: string
  signal?: string
  priority?: string
  website?: string
  source?: string
  sort_by?: string
  sort_order?: string
}

export interface ExportCreateRequest {
  export_type: ExportType
  scope: ExportScope
  record_ids?: number[]
  filters?: ExportFilterParams
}

export interface ExportStatusResponse {
  export_id: string
  status: "pending" | "processing" | "completed" | "failed"
  progress_percent: number
  records_processed: number
  total_records: number | null
  download_url: string | null
  error_message: string | null
}

const API_BASE =
  typeof window !== "undefined"
    ? "/api/proxy/v1"
    : `${(process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "")}/v1`

/**
 * Downloads a file blob from the API and triggers the native browser save.
 */
export async function downloadFileBlob(
  path: string,
  fallbackFilename: string,
  signal?: AbortSignal
): Promise<void> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`
  const url = `${API_BASE}${normalizedPath}`

  const res = await fetch(url, {
    method: "GET",
    credentials: "include",
    cache: "no-store",
    signal,
  })

  if (!res.ok) {
    let errorMessage = `Download failed with status ${res.status}`
    try {
      const errJson = await res.json()
      if (errJson?.detail) {
        errorMessage = errJson.detail
      }
    } catch {
      // res is not JSON
    }
    throw new Error(errorMessage)
  }

  // Determine filename from Content-Disposition header if present
  let filename = fallbackFilename
  const disposition = res.headers.get("Content-Disposition")
  if (disposition) {
    const match = /filename\*?=['"]?(?:UTF-\d['"]*)?([^;\r\n"']*)['"]?/i.exec(disposition)
    if (match && match[1]) {
      filename = decodeURIComponent(match[1].trim())
    }
  }

  const blob = await res.blob()
  const blobUrl = window.URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = blobUrl
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)

  // Clean up object URL after download is dispatched
  setTimeout(() => {
    window.URL.revokeObjectURL(blobUrl)
  }, 1000)
}

export interface RunExportOptions {
  request: ExportCreateRequest
  onProgress?: (status: ExportStatusResponse) => void
  signal?: AbortSignal
}

/**
 * Initiates an export job, polls until completion while notifying progress,
 * and automatically triggers the file download.
 */
export async function runExportAndDownload({
  request,
  onProgress,
  signal,
}: RunExportOptions): Promise<void> {
  // 1. Initiate job
  const initRes = await api.post<ExportStatusResponse>("/exports", request)
  if (!initRes || !initRes.export_id) {
    throw new Error("Failed to initiate export job.")
  }

  let job = initRes
  onProgress?.(job)

  // 2. Poll until completed or failed
  const pollIntervalMs = 500
  const maxPolls = 600 // 5 minutes timeout

  for (let pollCount = 0; pollCount < maxPolls; pollCount++) {
    if (signal?.aborted) {
      throw new DOMException("Export was cancelled.", "AbortError")
    }

    if (job.status === "completed") {
      break
    }

    if (job.status === "failed") {
      throw new Error(job.error_message || "Export processing failed.")
    }

    // Wait before next check
    await new Promise((resolve, reject) => {
      const timer = setTimeout(resolve, pollIntervalMs)
      if (signal) {
        signal.addEventListener(
          "abort",
          () => {
            clearTimeout(timer)
            reject(new DOMException("Export was cancelled.", "AbortError"))
          },
          { once: true }
        )
      }
    })

    job = await api.get<ExportStatusResponse>(`/exports/${job.export_id}`)
    onProgress?.(job)
  }

  if (job.status !== "completed") {
    throw new Error("Export timed out. Please try a narrower filter.")
  }

  // 3. Download CSV file
  const downloadPath = job.download_url || `/exports/${job.export_id}/download`
  const dateStr = new Date().toISOString().slice(0, 10)
  const defaultFilename = `${request.export_type}_export_${dateStr}.csv`

  await downloadFileBlob(downloadPath, defaultFilename, signal)
}
