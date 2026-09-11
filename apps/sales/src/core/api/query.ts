/**
 * Query string serialization utility for FastUI API requests.
 * Standardizes arrays, booleans, and nullish filtering across all feature API modules.
 */

export type QueryValue =
  | string
  | number
  | boolean
  | null
  | undefined
  | (string | number | boolean)[];

export type QueryParams = Record<string, QueryValue>;

/**
 * Builds a valid query string from a key-value params object.
 * Returns empty string if no valid parameters exist.
 */
export function buildQueryParams(params?: QueryParams): string {
  if (!params) return "";

  const searchParams = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === "") {
      continue;
    }

    if (Array.isArray(value)) {
      for (const item of value) {
        if (item !== null && item !== undefined && item !== "") {
          searchParams.append(key, String(item));
        }
      }
    } else {
      searchParams.set(key, String(value));
    }
  }

  const qs = searchParams.toString();
  return qs ? `?${qs}` : "";
}
