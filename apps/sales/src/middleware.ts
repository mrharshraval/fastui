import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

const AUTH_ROUTES = [
  "/login",
  "/signup",
  "/verify",
  "/forgot-password",
  "/reset-password",
]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const token = request.cookies.get("access_token")?.value

  // Allow static files, Next internals, public assets, and API routes
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/assets") ||
    pathname.startsWith("/brand") ||
    pathname.startsWith("/fonts") ||
    pathname.includes(".")
  ) {
    return NextResponse.next()
  }

  const isAuthRoute = AUTH_ROUTES.some((route) => pathname.startsWith(route))

  // 1. Unauthenticated users trying to access dashboard routes -> redirect to /login
  if (!token && !isAuthRoute) {
    const loginUrl = new URL("/login", request.url)
    return NextResponse.redirect(loginUrl)
  }

  // 2. Authenticated users trying to access auth routes (like /login) -> redirect to dashboard
  if (token && isAuthRoute) {
    const dashboardUrl = new URL("/", request.url)
    return NextResponse.redirect(dashboardUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
}
