/**
 * Shared Date & Timezone Utilities
 * =================================
 * Universal UTC storage and dynamic device timezone handling for reminders and timestamps.
 *
 * Rules:
 * 1. reminders.due_at is stored in UTC only.
 * 2. Display all reminder dates/times in the user's device timezone via
 *    Intl.DateTimeFormat().resolvedOptions().timeZone.
 * 3. Never hardcode IST, offsets, or server timezone.
 * 4. The date/time picker accepts and displays LOCAL device time.
 * 5. Convert local picker selection → UTC ISO before saving.
 * 6. Convert stored UTC → device local time when displaying/editing.
 *
 * Target Format:
 * e.g., "2026-09-02 20:50:08+00" → India device → "Sep 3, 2026 · 2:20 AM"
 */

/**
 * Returns the IANA time zone identifier of the user's current environment/device.
 * e.g. "Asia/Kolkata", "America/New_York", "Europe/London".
 */
export function getUserTimeZone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"
  } catch {
    return "UTC"
  }
}

/**
 * Safely parses any date input (UTC ISO string, PostgreSQL timestamptz string,
 * or existing Date instance) into a valid UTC Date object.
 *
 * Handles:
 * - "2026-09-02 20:50:08+00"
 * - "2026-09-02T20:50:08Z"
 * - "2026-09-02T20:50:08.123+00:00"
 * - "2026-09-02T20:50:08" (without timezone: assumed UTC)
 */
export function parseUtcDate(input?: string | Date | null): Date {
  if (!input) return new Date()
  if (input instanceof Date) return isNaN(input.getTime()) ? new Date() : input

  let cleaned = String(input).trim()
  if (!cleaned) return new Date()

  // Convert PostgreSQL space format "2026-09-02 20:50:08+00" to ISO "2026-09-02T20:50:08+00:00"
  if (cleaned.includes(" ") && !cleaned.includes("T")) {
    cleaned = cleaned.replace(" ", "T")
  }

  // If timezone offset is +00 or -00 (missing minutes), make it +00:00
  cleaned = cleaned.replace(/([+-]\d{2})$/, "$1:00")

  // If no timezone indicator is present, treat backend timestamp as UTC
  if (!cleaned.endsWith("Z") && !/[+-]\d{2}:\d{2}$/.test(cleaned)) {
    cleaned += "Z"
  }

  const parsed = new Date(cleaned)
  return isNaN(parsed.getTime()) ? new Date() : parsed
}

/**
 * Converts local picker components (date "YYYY-MM-DD" and time "HH:mm") into a UTC ISO-8601 string.
 *
 * Example:
 * In India (UTC+5:30):
 * localPartsToUtcIso("2026-09-03", "02:20") → "2026-09-02T20:50:00.000Z"
 */
export function localPartsToUtcIso(dateStr: string, timeStr: string): string {
  try {
    const [year, month, day] = dateStr.split("-").map(Number)
    const [hour, minute] = timeStr.split(":").map(Number)

    // Construct a Date object using local device time
    const localDate = new Date(year, (month || 1) - 1, day || 1, hour || 0, minute || 0, 0, 0)
    return localDate.toISOString()
  } catch {
    return new Date().toISOString()
  }
}

/**
 * Converts a stored UTC timestamp into local date ("YYYY-MM-DD") and time ("HH:mm")
 * parts in the user's device timezone for use in date/time pickers.
 */
export function utcIsoToLocalParts(utcInput: string | Date): {
  date: string // "YYYY-MM-DD"
  time: string // "HH:mm" (24h format for wheel picker)
  displayDate: string
  displayTime: string
} {
  const d = parseUtcDate(utcInput)
  const timeZone = getUserTimeZone()

  // Use Intl to format parts in the resolved device timezone
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })

  const parts = formatter.formatToParts(d)
  const partMap: Record<string, string> = {}
  for (const part of parts) {
    partMap[part.type] = part.value
  }

  const year = partMap.year || String(d.getFullYear())
  const month = partMap.month || String(d.getMonth() + 1).padStart(2, "0")
  const day = partMap.day || String(d.getDate()).padStart(2, "0")
  let hour = partMap.hour || "00"
  // If hour12: false returned "24", map to "00"
  if (hour === "24") hour = "00"
  const minute = partMap.minute || "00"

  const date = `${year}-${month}-${day}`
  const time = `${hour}:${minute}`

  return {
    date,
    time,
    displayDate: formatLocalDate(d),
    displayTime: formatLocalTime(d),
  }
}

/**
 * Formats a reminder UTC timestamp into the exact required format in the user's device timezone:
 * e.g., "2026-09-02 20:50:08+00" on India device → "Sep 3, 2026 · 2:20 AM"
 */
export function formatReminderDisplay(utcInput?: string | Date | null): string {
  if (!utcInput) return "No date"

  const d = parseUtcDate(utcInput)
  const timeZone = getUserTimeZone()

  // Date part: "Sep 3, 2026"
  const dateFormatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    month: "short",
    day: "numeric",
    year: "numeric",
  })

  // Time part: "2:20 AM"
  const timeFormatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  })

  const dateStr = dateFormatter.format(d)
  const timeStr = timeFormatter.format(d)

  return `${dateStr} · ${timeStr}`
}

/**
 * Formats a date in the user's device timezone: e.g. "Sep 3, 2026"
 */
export function formatLocalDate(utcInput?: string | Date | null): string {
  if (!utcInput) return ""
  const d = parseUtcDate(utcInput)
  const timeZone = getUserTimeZone()

  return new Intl.DateTimeFormat("en-US", {
    timeZone,
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(d)
}

/**
 * Formats a time in the user's device timezone: e.g. "2:20 AM"
 */
export function formatLocalTime(utcInput?: string | Date | null): string {
  if (!utcInput) return ""
  const d = parseUtcDate(utcInput)
  const timeZone = getUserTimeZone()

  return new Intl.DateTimeFormat("en-US", {
    timeZone,
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(d)
}

/**
 * Classifies a reminder's urgency into "overdue", "due_today", or "upcoming"
 * relative to the user's device timezone.
 */
export function getReminderUrgency(utcInput?: string | Date | null): "overdue" | "due_today" | "upcoming" {
  if (!utcInput) return "upcoming"
  const d = parseUtcDate(utcInput)
  const now = new Date()

  // If timestamp has passed
  if (d.getTime() < now.getTime()) {
    return "overdue"
  }

  // Check if it falls on the same calendar day in the device timezone
  const timeZone = getUserTimeZone()
  const dayFormatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "numeric",
    day: "numeric",
  })

  const dueDay = dayFormatter.format(d)
  const todayDay = dayFormatter.format(now)

  if (dueDay === todayDay) {
    return "due_today"
  }

  return "upcoming"
}
