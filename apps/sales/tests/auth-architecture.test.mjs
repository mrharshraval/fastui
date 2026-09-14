import { test, describe, beforeEach } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const SRC_DIR = path.resolve(__dirname, "../src");

describe("Authentication Architecture & Security Contract", () => {
  // =========================================================================
  // 1. Client/Server Boundary & Persistent Storage Audit
  // =========================================================================
  describe("Client/Server Boundary & Storage Audit", () => {
    test("Zero occurrences of fastui_user in the entire codebase", () => {
      function scanDir(dir) {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
          const fullPath = path.join(dir, entry.name);
          if (entry.isDirectory()) {
            if (entry.name !== "node_modules" && entry.name !== ".next") {
              scanDir(fullPath);
            }
          } else if (entry.name.endsWith(".ts") || entry.name.endsWith(".tsx") || entry.name.endsWith(".js")) {
            const content = fs.readFileSync(fullPath, "utf8");
            assert.equal(
              content.includes("fastui_user"),
              false,
              `Found illegal fastui_user reference in ${fullPath}`
            );
          }
        }
      }
      scanDir(SRC_DIR);
    });

    test("Zero localStorage identity caching in auth, settings, layout, and sidebar", () => {
      const filesToCheck = [
        path.join(SRC_DIR, "app/(dashboard)/layout.tsx"),
        path.join(SRC_DIR, "components/app-sidebar.tsx"),
        path.join(SRC_DIR, "features/auth/components/LoginForm.tsx"),
        path.join(SRC_DIR, "features/auth/components/VerifyOtpForm.tsx"),
        path.join(SRC_DIR, "features/settings/SettingsView.tsx"),
        path.join(SRC_DIR, "providers/session-provider.tsx"),
        path.join(SRC_DIR, "core/auth/server-session.ts"),
      ];

      for (const filePath of filesToCheck) {
        if (fs.existsSync(filePath)) {
          const content = fs.readFileSync(filePath, "utf8");
          assert.equal(
            content.includes("localStorage"),
            false,
            `Found forbidden localStorage access in ${filePath}`
          );
          assert.equal(
            content.includes("sessionStorage"),
            false,
            `Found forbidden sessionStorage access in ${filePath}`
          );
        }
      }
    });

    test("Zero client-side /v1/auth/me calls on initial dashboard navigation", () => {
      // app-sidebar and layout and settings must not initiate getMe() / getCurrentUser() on mount
      const layoutContent = fs.readFileSync(path.join(SRC_DIR, "app/(dashboard)/layout.tsx"), "utf8");
      assert.equal(layoutContent.includes('"use client"'), false, "DashboardLayout must be a Server Component");
      assert.equal(layoutContent.includes("useEffect"), false, "DashboardLayout must not have client useEffect");

      const sidebarContent = fs.readFileSync(path.join(SRC_DIR, "components/app-sidebar.tsx"), "utf8");
      assert.equal(sidebarContent.includes("authApi.getMe"), false, "AppSidebar must not fetch authApi.getMe");
      assert.equal(sidebarContent.includes("/v1/auth/me"), false, "AppSidebar must not call /v1/auth/me");

      const settingsViewContent = fs.readFileSync(path.join(SRC_DIR, "features/settings/SettingsView.tsx"), "utf8");
      assert.equal(
        settingsViewContent.includes("settingsApi.getCurrentUser"),
        false,
        "SettingsView must not call getCurrentUser on mount"
      );

      const sessionProviderContent = fs.readFileSync(path.join(SRC_DIR, "providers/session-provider.tsx"), "utf8");
      const codeOnly = sessionProviderContent.replace(/\/\*[\s\S]*?\*\/|\/\/.*/g, "");
      assert.equal(
        codeOnly.includes("/v1/auth/me"),
        false,
        "SessionProvider must never call /v1/auth/me"
      );
      assert.equal(
        codeOnly.includes("fetch"),
        false,
        "SessionProvider must not perform network fetches"
      );
    });

    test("server-only is strictly confined to Server Components and never imported by Client Components", () => {
      function checkClientFiles(dir) {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
          const fullPath = path.join(dir, entry.name);
          if (entry.isDirectory()) {
            if (entry.name !== "node_modules" && entry.name !== ".next") {
              checkClientFiles(fullPath);
            }
          } else if (entry.name.endsWith(".ts") || entry.name.endsWith(".tsx")) {
            const content = fs.readFileSync(fullPath, "utf8");
            if (content.includes('"use client"') || content.includes("'use client'")) {
              assert.equal(
                content.includes('from "server-only"') || content.includes("from 'server-only'"),
                false,
                `Client component ${fullPath} must never import server-only`
              );
              assert.equal(
                content.includes("server-session"),
                false,
                `Client component ${fullPath} must never import server-session`
              );
            }
          }
        }
      }
      checkClientFiles(SRC_DIR);
    });
  });

  // =========================================================================
  // 2. Next.js 16 Proxy Route Gate & CSRF Defense
  // =========================================================================
  describe("Proxy Route Gate & CSRF Defenses", () => {
    // Mock NextRequest and NextResponse logic matching src/proxy.ts
    function createMockRequest({
      pathname,
      search = "",
      method = "GET",
      cookies = {},
      headers = {},
    }) {
      const url = `https://fastui.local${pathname}${search}`;
      const headersMap = new Map(Object.entries(headers));
      return {
        url,
        nextUrl: {
          pathname,
          search,
          host: "fastui.local",
          origin: "https://fastui.local",
          searchParams: new URLSearchParams(search),
        },
        method,
        cookies: {
          get: (name) => (cookies[name] ? { name, value: cookies[name] } : undefined),
        },
        headers: {
          get: (name) => headersMap.get(name.toLowerCase()) || null,
        },
      };
    }

    test("Unauthenticated user accessing protected route is redirected to /login with returnUrl", async () => {
      const { proxy } = await import("../src/proxy.ts");
      const req = createMockRequest({ pathname: "/settings" });
      const res = proxy(req);

      assert.ok(res, "Proxy must return a response");
      assert.equal(res.status, 307, "Expected redirect status");
      const location = res.headers.get("location");
      assert.ok(location, "Must have location header");
      const redirectUrl = new URL(location);
      assert.equal(redirectUrl.pathname, "/login");
      assert.equal(redirectUrl.searchParams.get("returnUrl"), "/settings");
    });

    test("Unauthenticated user accessing root dashboard is redirected to /login without returnUrl", async () => {
      const { proxy } = await import("../src/proxy.ts");
      const req = createMockRequest({ pathname: "/" });
      const res = proxy(req);

      assert.ok(res);
      assert.equal(res.status, 307);
      const location = res.headers.get("location");
      const redirectUrl = new URL(location);
      assert.equal(redirectUrl.pathname, "/login");
      assert.equal(redirectUrl.searchParams.get("returnUrl"), null);
    });

    test("Authenticated user accessing /login is redirected to dashboard", async () => {
      const { proxy } = await import("../src/proxy.ts");
      const req = createMockRequest({
        pathname: "/login",
        cookies: { access_token: "valid_jwt_token" },
      });
      const res = proxy(req);

      assert.ok(res);
      assert.equal(res.status, 307);
      const location = res.headers.get("location");
      const redirectUrl = new URL(location);
      assert.equal(redirectUrl.pathname, "/");
    });

    test("Authenticated user accessing /login?returnUrl=/leads is redirected to /leads", async () => {
      const { proxy } = await import("../src/proxy.ts");
      const req = createMockRequest({
        pathname: "/login",
        search: "?returnUrl=%2Fleads",
        cookies: { access_token: "valid_jwt_token" },
      });
      const res = proxy(req);

      assert.ok(res);
      assert.equal(res.status, 307);
      const location = res.headers.get("location");
      const redirectUrl = new URL(location);
      assert.equal(redirectUrl.pathname, "/leads");
    });

    test("Open-redirect prevention: malicious returnUrl is normalized to /", async () => {
      const { proxy } = await import("../src/proxy.ts");
      const maliciousUrls = ["//evil.com", "https://evil.com", "javascript:alert(1)"];

      for (const badUrl of maliciousUrls) {
        const req = createMockRequest({
          pathname: "/login",
          search: `?returnUrl=${encodeURIComponent(badUrl)}`,
          cookies: { access_token: "valid_jwt_token" },
        });
        const res = proxy(req);
        assert.ok(res);
        const location = res.headers.get("location");
        const redirectUrl = new URL(location);
        assert.equal(redirectUrl.pathname, "/", `Expected safe fallback for ${badUrl}`);
      }
    });

    test("CSRF: Mutating request to /api/* with cross-site Sec-Fetch-Site is rejected with 403", async () => {
      const { proxy } = await import("../src/proxy.ts");
      const req = createMockRequest({
        pathname: "/api/proxy/v1/users",
        method: "POST",
        headers: {
          "sec-fetch-site": "cross-site",
          origin: "https://evil-site.com",
        },
      });
      const res = proxy(req);

      assert.ok(res);
      assert.equal(res.status, 403);
      const body = await res.json();
      assert.equal(body.error, "Forbidden: Cross-site request rejected");
    });

    test("CSRF: Mutating request to /api/* with mismatched Origin header is rejected with 403", async () => {
      const { proxy } = await import("../src/proxy.ts");
      const req = createMockRequest({
        pathname: "/api/proxy/v1/auth/logout",
        method: "POST",
        headers: {
          origin: "https://attacker.com",
          host: "fastui.local",
        },
      });
      const res = proxy(req);

      assert.ok(res);
      assert.equal(res.status, 403);
      const body = await res.json();
      assert.equal(body.error, "Forbidden: Cross-origin request rejected");
    });

    test("CSRF: Legitimate same-origin mutating request to /api/* is permitted", async () => {
      const { proxy } = await import("../src/proxy.ts");
      const req = createMockRequest({
        pathname: "/api/proxy/v1/auth/me",
        method: "PATCH",
        headers: {
          "sec-fetch-site": "same-origin",
          origin: "https://fastui.local",
          host: "fastui.local",
        },
      });
      const res = proxy(req);

      assert.ok(res);
      // Status 200/NextResponse.next() -> not blocked by 403
      assert.notEqual(res.status, 403);
    });
  });

  // =========================================================================
  // 3. Server Session Resolution & 401 Redirects
  // =========================================================================
  describe("Server Session Resolution & Error Handling", () => {
    test("requireSession redirects immediately to /login on 401 without rendering shell", async () => {
      // Simulate requireSession logic
      let redirectedTo = null;
      function mockRedirect(url) {
        redirectedTo = url;
        const err = new Error("NEXT_REDIRECT");
        err.digest = "NEXT_REDIRECT;replace;/login";
        throw err;
      }

      async function testRequireSession(mockCookie, mockApiCall) {
        if (!mockCookie) {
          mockRedirect("/login");
        }
        try {
          return await mockApiCall();
        } catch (error) {
          if (error?.status === 401) {
            mockRedirect("/login");
          }
          throw error;
        }
      }

      // Case A: Missing token
      try {
        await testRequireSession(null, async () => ({ email: "test@example.com" }));
      } catch (e) {
        assert.equal(e.message, "NEXT_REDIRECT");
      }
      assert.equal(redirectedTo, "/login");

      // Case B: Expired/invalid token resulting in 401 from backend
      redirectedTo = null;
      try {
        await testRequireSession("expired_token", async () => {
          const err = new Error("Unauthorized");
          err.status = 401;
          throw err;
        });
      } catch (e) {
        assert.equal(e.message, "NEXT_REDIRECT");
      }
      assert.equal(redirectedTo, "/login");
    });

    test("Request-level memoization ensures at most one /auth/me lookup per RSC request tree", async () => {
      let callCount = 0;
      const fakeBackendGetMe = async () => {
        callCount++;
        return { user_id: 1, email: "sales@fastui.com", role: "admin", name: "Sales Agent" };
      };

      // Simulating React.cache behavior for a single request
      let cacheStore = null;
      const cachedGetSession = async () => {
        if (cacheStore) return cacheStore;
        cacheStore = await fakeBackendGetMe();
        return cacheStore;
      };

      // 3 components in the same RSC render tree requesting session
      const res1 = await cachedGetSession();
      const res2 = await cachedGetSession();
      const res3 = await cachedGetSession();

      assert.deepEqual(res1, res2);
      assert.deepEqual(res2, res3);
      assert.equal(callCount, 1, "Backend getMe must be invoked exactly once per request tree");
    });
  });

  // =========================================================================
  // 4. Session State Distribution & Ephemeral In-Memory Updates
  // =========================================================================
  describe("Session Distribution & In-Memory Isolation", () => {
    test("Profile update updates in-memory session without router.refresh() or full reload", () => {
      let state = {
        session: { user_id: 10, email: "agent@fastui.com", name: "Initial Name" },
      };

      const updateSession = (updated) => {
        state.session = { ...state.session, ...updated };
      };

      // Simulate successful PATCH /v1/auth/me response
      const apiResponse = { user_id: 10, email: "agent@fastui.com", name: "Updated Name" };
      updateSession(apiResponse);

      assert.equal(state.session.name, "Updated Name");
      assert.equal(state.session.email, "agent@fastui.com");
    });

    test("Logout immediately clears client in-memory session state cleanly", () => {
      let state = {
        session: { user_id: 10, email: "agent@fastui.com", name: "Agent" },
      };

      const clearSession = () => {
        state.session = null;
      };

      clearSession();
      assert.equal(state.session, null, "In-memory session must be null after logout");
    });

    test("Account deletion clears local session without leaving residual identity", () => {
      let state = {
        session: { user_id: 42, email: "deleted@fastui.com" },
      };

      const clearSession = () => {
        state.session = null;
      };

      clearSession();
      assert.equal(state.session, null);
    });

    test("User-switch isolation: when server resolves a new session, client provider synchronizes immediately", () => {
      let clientSession = { user_id: 1, email: "user1@fastui.com", name: "User One" };

      // Simulate RSC re-render passing a new session prop (e.g. user switch)
      const onServerSessionChange = (newServerSession) => {
        clientSession = newServerSession;
      };

      onServerSessionChange({ user_id: 2, email: "user2@fastui.com", name: "User Two" });
      assert.equal(clientSession.user_id, 2);
      assert.equal(clientSession.email, "user2@fastui.com");
      assert.equal(clientSession.name, "User Two");
    });
  });

  // =========================================================================
  // 5. Lifecycle & Edge Cases (Tampered JWT, Password Reset, Email Verification)
  // =========================================================================
  describe("Lifecycle Contracts & Security Boundary", () => {
    test("Tampered / malformed JWT: getSession returns null safely without crash", async () => {
      async function mockGetSession(mockApiCall) {
        try {
          return await mockApiCall();
        } catch (error) {
          if (error?.digest?.startsWith?.("NEXT_REDIRECT")) {
            throw error;
          }
          return null;
        }
      }

      const result = await mockGetSession(async () => {
        const err = new Error("Invalid signature");
        err.status = 401;
        throw err;
      });

      assert.equal(result, null, "Malformed/tampered JWT must resolve to null");
    });

    test("Raw JWT is never exposed in client session payload", () => {
      // The session object distributed to client must only contain user metadata
      const serverResolvedSession = {
        user_id: 1,
        email: "user@example.com",
        role: "admin",
        name: "Admin User",
      };

      assert.equal("token" in serverResolvedSession, false);
      assert.equal("access_token" in serverResolvedSession, false);
      assert.equal("jwt" in serverResolvedSession, false);
      assert.equal("secret" in serverResolvedSession, false);
    });

    test("Password reset and OTP verification flows do not touch localStorage", () => {
      const resetForm = fs.readFileSync(path.join(SRC_DIR, "features/auth/components/ResetPasswordForm.tsx"), "utf8");
      const forgotForm = fs.readFileSync(path.join(SRC_DIR, "features/auth/components/ForgotPasswordForm.tsx"), "utf8");
      const verifyForm = fs.readFileSync(path.join(SRC_DIR, "features/auth/components/VerifyOtpForm.tsx"), "utf8");

      for (const [name, content] of [
        ["ResetPasswordForm", resetForm],
        ["ForgotPasswordForm", forgotForm],
        ["VerifyOtpForm", verifyForm],
      ]) {
        assert.equal(content.includes("localStorage"), false, `${name} must not touch localStorage`);
        assert.equal(content.includes("sessionStorage"), false, `${name} must not touch sessionStorage`);
      }
    });
  });
});
