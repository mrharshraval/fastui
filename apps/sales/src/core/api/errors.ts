/**
 * Standardized API Error class for FastUI.
 * Formats status codes, request correlation IDs, and structured FastAPI validation errors.
 */

export interface ApiErrorDetail {
  loc?: (string | number)[];
  msg?: string;
  type?: string;
  [key: string]: unknown;
}

export class ApiError extends Error {
  public readonly status: number;
  public readonly code?: string;
  public readonly details?: unknown;
  public readonly requestId?: string;

  constructor(
    message: string,
    status: number,
    code?: string,
    details?: unknown,
    requestId?: string
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.requestId = requestId;
    Object.setPrototypeOf(this, ApiError.prototype);
  }

  /**
   * Parses backend error response bodies (including FastAPI 422 arrays).
   */
  public static fromResponse(
    status: number,
    payload: unknown,
    defaultMessage = "Request failed"
  ): ApiError {
    let message = defaultMessage;
    let code: string | undefined = `HTTP_${status}`;
    let details: unknown = undefined;
    let requestId: string | undefined = undefined;

    if (payload && typeof payload === "object") {
      const data = payload as Record<string, unknown>;

      // Extract request_id if present
      if (typeof data.request_id === "string") {
        requestId = data.request_id;
      }

      // Handle structured envelope: { error: { code, message, details, request_id } }
      if (data.error && typeof data.error === "object") {
        const errorEnv = data.error as Record<string, unknown>;
        if (typeof errorEnv.message === "string") message = errorEnv.message;
        if (typeof errorEnv.code === "string") code = errorEnv.code;
        if (errorEnv.details !== undefined) details = errorEnv.details;
        if (typeof errorEnv.request_id === "string") requestId = errorEnv.request_id;
      }
      // Handle standard FastAPI 422: { detail: [{ loc, msg, type }] }
      else if (Array.isArray(data.detail)) {
        const detailList = data.detail as ApiErrorDetail[];
        message = detailList
          .map((d) => {
            const field = Array.isArray(d.loc) ? d.loc.filter((part) => part !== "body").join(".") : "";
            return field ? `${field}: ${d.msg}` : (d.msg ?? "Validation error");
          })
          .join("; ");
        details = detailList;
        code = "VALIDATION_ERROR";
      }
      // Handle standard detail string: { detail: "error message" }
      else if (typeof data.detail === "string") {
        message = data.detail;
      }
    }

    return new ApiError(message, status, code, details, requestId);
  }
}
