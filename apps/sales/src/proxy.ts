import { NextResponse } from "next/server.js";
import type { NextRequest } from "next/server.js";

const AUTH_ROUTES = [
  "/login",
  "/signup",
  "/verify",
  "/forgot-password",
  "/reset-password",
];

const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

/**
 * Validates a returnUrl query parameter to protect against open redirects.
 * Must start with a single "/" and not "//".
 */
function getSafeReturnUrl(candidate: string | null): string {
  if (!candidate) return "/";
  if (candidate.startsWith("/") && !candidate.startsWith("//")) {
    return candidate;
  }
  return "/";
}

/**
 * Canonical Next.js 16 request-interception and early routing gate.
 * 
 * Responsibilities:
 * 1. CSRF Defense for mutating API requests (Origin matching + Fetch Metadata Sec-Fetch-Site).
 * 2. Early routing gate redirecting unauthenticated users to /login with returnUrl.
 * 3. Redirecting authenticated users away from public auth pages.
 * 
 * Note: This is an early routing/security gate only. Authoritative cryptographic
 * JWT validation, signature verification, and identity lookup are performed by
 * the backend during server session resolution.
 */
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("access_token")?.value;

  // 1. CSRF Defense for mutating API requests (/api/*)
  if (pathname.startsWith("/api") && MUTATING_METHODS.has(request.method)) {
    const secFetchSite = request.headers.get("sec-fetch-site");
    if (secFetchSite === "cross-site") {
      return new NextResponse(
        JSON.stringify({ error: "Forbidden: Cross-site request rejected" }),
        { status: 403, headers: { "Content-Type": "application/json" } }
      );
    }

    const origin = request.headers.get("origin");
    if (origin) {
      try {
        const originUrl = new URL(origin);
        const hostHeader = request.headers.get("host") || request.nextUrl.host;
        const originHost = originUrl.host;
        if (originHost !== hostHeader) {
          return new NextResponse(
            JSON.stringify({ error: "Forbidden: Cross-origin request rejected" }),
            { status: 403, headers: { "Content-Type": "application/json" } }
          );
        }
      } catch {
        return new NextResponse(
          JSON.stringify({ error: "Forbidden: Invalid origin header" }),
          { status: 403, headers: { "Content-Type": "application/json" } }
        );
      }
    }
  }

  // 2. Allow static files, Next.js internals, public assets, and API routes past the page route gate
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/assets") ||
    pathname.startsWith("/brand") ||
    pathname.startsWith("/fonts") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  const isAuthRoute = AUTH_ROUTES.some((route) => pathname.startsWith(route));

  // 3. Unauthenticated users trying to access protected dashboard routes -> redirect to /login with returnUrl
  if (!token && !isAuthRoute) {
    const loginUrl = new URL("/login", request.url);
    if (pathname !== "/") {
      const returnUrl = `${pathname}${request.nextUrl.search}`;
      loginUrl.searchParams.set("returnUrl", returnUrl);
    }
    return NextResponse.redirect(loginUrl);
  }

  // 4. Authenticated users trying to access public auth routes -> redirect to returnUrl or dashboard
  if (token && isAuthRoute) {
    const returnUrlParam = request.nextUrl.searchParams.get("returnUrl");
    const targetPath = getSafeReturnUrl(returnUrlParam);
    const destinationUrl = new URL(targetPath, request.url);
    return NextResponse.redirect(destinationUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match only page/API routes. Exclude:
     *   - _next/static  — Next.js static files
     *   - _next/image   — Next.js image optimisation
     *   - _next/webpack-hmr — HMR websocket
     *   - assets, brand, fonts — public static assets
     *   - sw.js, manifest.json — PWA files
     *   - favicon.ico
     *   - Any path ending in a file extension (images, SVGs, etc.)
     */
    "/((?!_next/static|_next/image|_next/webpack-hmr|assets|brand|fonts|sw\\.js|manifest\\.json|favicon\\.ico|.*\\..*).*)",
  ],
};
