export function jsonResponse(data: unknown, status: number = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
    },
  })
}

export function errorResponse(message: string, status: number = 500, details?: unknown): Response {
  const body: Record<string, unknown> = { error: message }
  if (details !== undefined) {
    body.details = details
  }
  return jsonResponse(body, status)
}
