/**
 * Shared Date & Timezone Utilities
 * Universal UTC storage and dynamic device timezone handling.
 */

export function getUserTimeZone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

export function parseUtcDate(input?: string | Date | null): Date {
  if (!input) return new Date();
  if (input instanceof Date) return isNaN(input.getTime()) ? new Date() : input;

  let cleaned = String(input).trim();
  if (!cleaned) return new Date();

  if (cleaned.includes(" ") && !cleaned.includes("T")) {
    cleaned = cleaned.replace(" ", "T");
  }

  cleaned = cleaned.replace(/([+-]\d{2})$/, "$1:00");

  if (!cleaned.endsWith("Z") && !/[+-]\d{2}:\d{2}$/.test(cleaned)) {
    cleaned += "Z";
  }

  const parsed = new Date(cleaned);
  return isNaN(parsed.getTime()) ? new Date() : parsed;
}

export function localPartsToUtcIso(dateStr: string, timeStr: string): string {
  try {
    const [year, month, day] = dateStr.split("-").map(Number);
    const [hour, minute] = timeStr.split(":").map(Number);
    const localDate = new Date(year, (month || 1) - 1, day || 1, hour || 0, minute || 0, 0, 0);
    return localDate.toISOString();
  } catch {
    return new Date().toISOString();
  }
}

export function utcIsoToLocalParts(utcInput: string | Date): {
  date: string;
  time: string;
  displayDate: string;
  displayTime: string;
} {
  const d = parseUtcDate(utcInput);
  const timeZone = getUserTimeZone();

  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });

  const parts = formatter.formatToParts(d);
  const partMap: Record<string, string> = {};
  for (const part of parts) {
    partMap[part.type] = part.value;
  }

  const year = partMap.year || String(d.getFullYear());
  const month = partMap.month || String(d.getMonth() + 1).padStart(2, "0");
  const day = partMap.day || String(d.getDate()).padStart(2, "0");
  let hour = partMap.hour || "00";
  if (hour === "24") hour = "00";
  const minute = partMap.minute || "00";

  const date = `${year}-${month}-${day}`;
  const time = `${hour}:${minute}`;

  return {
    date,
    time,
    displayDate: formatLocalDate(d),
    displayTime: formatLocalTime(d),
  };
}

export function formatReminderDisplay(utcInput?: string | Date | null): string {
  if (!utcInput) return "No date";

  const d = parseUtcDate(utcInput);
  const timeZone = getUserTimeZone();

  const dateFormatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  const timeFormatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });

  const dateStr = dateFormatter.format(d);
  const timeStr = timeFormatter.format(d);

  return `${dateStr} · ${timeStr}`;
}

export function formatLocalDate(utcInput?: string | Date | null): string {
  if (!utcInput) return "";
  const d = parseUtcDate(utcInput);
  const timeZone = getUserTimeZone();

  return new Intl.DateTimeFormat("en-US", {
    timeZone,
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(d);
}

export function formatLocalTime(utcInput?: string | Date | null): string {
  if (!utcInput) return "";
  const d = parseUtcDate(utcInput);
  const timeZone = getUserTimeZone();

  return new Intl.DateTimeFormat("en-US", {
    timeZone,
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  }).format(d);
}

export function getReminderUrgency(utcInput?: string | Date | null): "overdue" | "due_today" | "upcoming" {
  if (!utcInput) return "upcoming";
  const d = parseUtcDate(utcInput);
  const now = new Date();

  if (d.getTime() < now.getTime()) {
    return "overdue";
  }

  const timeZone = getUserTimeZone();
  const dayFormatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "numeric",
    day: "numeric",
  });

  const dueDay = dayFormatter.format(d);
  const todayDay = dayFormatter.format(now);

  if (dueDay === todayDay) {
    return "due_today";
  }

  return "upcoming";
}
