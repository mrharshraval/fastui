import { ApiError } from "./errors";
import { buildQueryParams, type QueryParams } from "./query";

const API_BASE =
  typeof window !== "undefined"
    ? "/api/proxy"
    : `${(process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "")}`;

export interface RequestOptions extends Omit<RequestInit, "body"> {
  params?: QueryParams;
  body?: unknown;
}

/**
 * Low-level HTTP transport client.
 * Handles correlation IDs, credentials, 204 No Content, cancellation signals,
 * and FastAPI 422 error normalization.
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { params, body, headers: customHeaders, ...init } = options;

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const queryString = buildQueryParams(params);
  const url = `${API_BASE}${normalizedPath}${queryString}`;

  const correlationId =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : undefined;

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(correlationId ? { "X-Correlation-ID": correlationId } : {}),
  };

  // On the server, forward the client request cookies so backend session authentication succeeds
  if (typeof window === "undefined") {
    try {
      const { cookies } = await import("next/headers");
      const cookieStore = await cookies();
      const cookieHeader = cookieStore.toString();
      if (cookieHeader) {
        headers["Cookie"] = cookieHeader;
      }
    } catch {
      // In build-time static generation or non-request context, next/headers might throw
    }
  }

  let serializedBody: BodyInit | undefined = undefined;
  if (body !== undefined && body !== null) {
    if (body instanceof FormData || body instanceof URLSearchParams || typeof body === "string") {
      serializedBody = body;
    } else {
      headers["Content-Type"] = "application/json";
      serializedBody = JSON.stringify(body);
    }
  }

  const response = await fetch(url, {
    ...init,
    body: serializedBody,
    credentials: "include",
    cache: init.cache ?? "no-store",
    headers: {
      ...headers,
      ...(customHeaders as Record<string, string> | undefined),
    },
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({ detail: response.statusText }));
    throw ApiError.fromResponse(response.status, errorPayload, `Request to ${path} failed with status ${response.status}`);
  }

  // Handle 204 No Content or empty responses
  if (response.status === 204 || response.headers.get("content-length") === "0") {
    return undefined as unknown as T;
  }

  // Check content-type before attempting JSON parsing
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }

  return (await response.text()) as unknown as T;
}

export const client = {
  get: <T>(path: string, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "GET" }),

  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "POST", body }),

  put: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "PUT", body }),

  patch: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "PATCH", body }),

  delete: <T>(path: string, options?: Omit<RequestOptions, "method">) =>
    request<T>(path, { ...options, method: "DELETE" }),
};

// Aliased export for compatibility with existing imports during migration
export const api = client;
