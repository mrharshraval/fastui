type LogLevel = "info" | "warn" | "error"

export type LogMetadata = Record<string, unknown> | Record<string, any>

function formatLog(level: LogLevel, event: string, metadata?: LogMetadata): string {
  const sanitized: Record<string, unknown> = {}
  if (metadata) {
    for (const [key, val] of Object.entries(metadata)) {
      // Guard against logging secrets, private keys, or credentials
      if (
        /key|secret|token|password|auth|credential/i.test(key) &&
        typeof val === "string"
      ) {
        sanitized[key] = "[REDACTED]"
      } else if (key === "endpoint" && typeof val === "string") {
        // Truncate full push endpoints for privacy/safety
        sanitized[key] = val.slice(0, 35) + "..."
      } else {
        sanitized[key] = val
      }
    }
  }

  return JSON.stringify({
    timestamp: new Date().toISOString(),
    level,
    event,
    ...sanitized,
  })
}

export const logger = {
  info(event: string, metadata?: LogMetadata) {
    console.log(formatLog("info", event, metadata))
  },
  warn(event: string, metadata?: LogMetadata) {
    console.warn(formatLog("warn", event, metadata))
  },
  error(event: string, metadata?: LogMetadata) {
    console.error(formatLog("error", event, metadata))
  },
}
