"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AlertCircle } from "lucide-react";
import { AuthFormContainer } from "./AuthFormContainer";
import { authApi } from "../api";

const BASE_INPUT =
  "w-full bg-transparent rounded-full h-12 px-4 text-sm placeholder:text-muted-foreground border transition-all outline-none";
const INPUT_OK = `${BASE_INPUT} border-border dark:border-white/20 text-foreground hover:border-foreground/60 focus:border-foreground focus:ring-1 focus:ring-foreground/20`;
const INPUT_ERR = `${BASE_INPUT} border-destructive text-foreground focus:border-destructive hover:border-destructive ring-1 ring-destructive/30`;

function FieldError({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-1.5 mt-1 text-destructive">
      <AlertCircle className="size-3.5 mt-0.5 shrink-0" />
      <p className="text-xs leading-tight font-medium">{message}</p>
    </div>
  );
}

export function LoginForm() {
  const router = useRouter();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [identifierError, setIdentifierError] = useState("");
  const [passwordError, setPasswordError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    let valid = true;
    if (!identifier) {
      setIdentifierError("Enter your email.");
      valid = false;
    } else setIdentifierError("");
    if (!password) {
      setPasswordError("Enter your password.");
      valid = false;
    } else setPasswordError("");
    if (!valid) return;
    setLoading(true);
    try {
      const res = await authApi.login({ email: identifier, password });
      if (res && res.user) {
        localStorage.setItem("fastui_user", JSON.stringify(res.user));
      }
      router.push("/");
      router.refresh();
    } catch (err: unknown) {
      setPasswordError(
        err instanceof Error ? err.message : "Invalid email or password"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthFormContainer
      title="Log in"
      footerText="Don't have an account?"
      footerLinkText="Sign up"
      footerLinkHref="/signup"
    >
      <form onSubmit={handleLogin} className="w-full space-y-4">
        <div className="space-y-1.5 flex flex-col items-start w-full">
          <Label
            htmlFor="identifier"
            className="text-sm font-bold text-foreground tracking-tight"
          >
            Email
          </Label>
          <Input
            id="identifier"
            type="email"
            placeholder="name@domain.com"
            value={identifier}
            onChange={(e) => {
              setIdentifier(e.target.value);
              if (identifierError) setIdentifierError("");
            }}
            aria-invalid={!!identifierError}
            className={identifierError ? INPUT_ERR : INPUT_OK}
            disabled={loading}
          />
          {identifierError && <FieldError message={identifierError} />}
        </div>

        <div className="space-y-1.5 flex flex-col items-start w-full">
          <div className="flex items-center justify-between w-full">
            <Label
              htmlFor="password"
              className="text-sm font-bold text-foreground tracking-tight"
            >
              Password
            </Label>
            <a
              href="/forgot-password"
              className="text-xs text-muted-foreground hover:text-foreground font-medium transition-colors"
            >
              Forgot password?
            </a>
          </div>
          <Input
            id="password"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              if (passwordError) setPasswordError("");
            }}
            aria-invalid={!!passwordError}
            className={passwordError ? INPUT_ERR : INPUT_OK}
            disabled={loading}
          />
          {passwordError && <FieldError message={passwordError} />}
        </div>

        <Button
          type="submit"
          disabled={loading}
          className="w-full h-12 rounded-full font-semibold text-sm mt-6 cursor-pointer bg-primary text-primary-foreground disabled:opacity-50"
        >
          {loading ? "Logging in…" : "Log in"}
        </Button>
      </form>
    </AuthFormContainer>
  );
}
