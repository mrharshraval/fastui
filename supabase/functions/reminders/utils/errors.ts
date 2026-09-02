export class AppError extends Error {
  readonly statusCode: number

  constructor(message: string, statusCode: number = 500) {
    super(message)
    this.name = "AppError"
    this.statusCode = statusCode
  }
}

export class UnauthorizedError extends AppError {
  constructor(message: string = "Unauthorized access: valid secret API key required") {
    super(message, 401)
    this.name = "UnauthorizedError"
  }
}

export class MethodNotAllowedError extends AppError {
  constructor(message: string = "Method not allowed") {
    super(message, 405)
    this.name = "MethodNotAllowedError"
  }
}

export class ConfigError extends AppError {
  constructor(message: string) {
    super(message, 500)
    this.name = "ConfigError"
  }
}
