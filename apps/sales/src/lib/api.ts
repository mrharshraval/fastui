const API_BASE =
  typeof window !== "undefined"
    ? "/api/proxy/v1"
    : `${(process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "")}/v1`

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`
  const url = `${API_BASE}${normalizedPath}`
  const correlationId = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : undefined

  const headers: Record<string, string> = {
    ...(correlationId ? { "X-Correlation-ID": correlationId } : {}),
  }
  if (init?.body) {
    headers["Content-Type"] = "application/json"
  }

  const res = await fetch(url, {
    ...init,
    credentials: "include",
    cache: "no-store",
    headers: {
      ...headers,
      ...init?.headers,
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw Object.assign(new Error(err.detail ?? "Request failed"), { status: res.status })
  }
  if (res.status === 204 || res.headers.get("content-length") === "0") {
    return undefined as unknown as T
  }
  return res.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: body !== undefined ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body !== undefined ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "DELETE", body: body !== undefined ? JSON.stringify(body) : undefined }),
}


