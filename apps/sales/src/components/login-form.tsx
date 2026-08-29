"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AlertCircle } from "lucide-react"
import { AuthFormContainer } from "./auth-form-container"
import { api } from "@/lib/api"

const BASE_INPUT = "w-full bg-transparent rounded-full h-12 px-3 text-base placeholder:text-muted-foreground"
const INPUT_OK = `${BASE_INPUT} border-border text-foreground hover:border-foreground focus:border-foreground`
const INPUT_ERR = `${BASE_INPUT} border-destructive text-destructive focus:border-destructive hover:border-destructive`

function FieldError({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-1.5 mt-1 text-destructive">
      <AlertCircle className="size-4 mt-0.5 shrink-0" />
      <p className="text-sm leading-tight font-medium">{message}</p>
    </div>
  )
}

export function LoginForm() {
  const router = useRouter()
  const [identifier, setIdentifier] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [identifierError, setIdentifierError] = useState("")
  const [passwordError, setPasswordError] = useState("")

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    let valid = true
    if (!identifier) { setIdentifierError("Please enter your email or username."); valid = false } else setIdentifierError("")
    if (!password) { setPasswordError("Please enter your password."); valid = false } else setPasswordError("")
    if (!valid) return
    setLoading(true)
    try {
      const res = await api.post<{ user?: { id: number; email: string; role: string } }>("/auth/login", { email: identifier, password })
      if (res?.user) {
        localStorage.setItem("fastui_user", JSON.stringify(res.user))
      }
      router.push("/")
      router.refresh()
    } catch (err: unknown) {
      setPasswordError(err instanceof Error ? err.message : "Invalid email or password")
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthFormContainer
      title="Log in"
      footerText="Don't have an account?"
      footerLinkText="Sign up"
      footerLinkHref="/signup"
    >
      <form onSubmit={handleLogin} className="w-full space-y-4">
        <div className="space-y-1.5 flex flex-col items-start w-full">
          <Label htmlFor="identifier" className="text-sm font-bold text-foreground">
            Email or username
          </Label>
          <Input
            id="identifier"
            type="text"
            placeholder="Email or username"
            value={identifier}
            onChange={(e) => { setIdentifier(e.target.value); if (identifierError) setIdentifierError("") }}
            aria-invalid={!!identifierError}
            className={identifierError ? INPUT_ERR : INPUT_OK}
            disabled={loading}
          />
          {identifierError && <FieldError message={identifierError} />}
        </div>

        <div className="space-y-1.5 flex flex-col items-start w-full">
          <div className="flex w-full items-center justify-between">
            <Label htmlFor="password" className="text-sm font-bold text-foreground">
              Password
            </Label>
            <Link
              href="/forgot-password"
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <Input
            id="password"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => { setPassword(e.target.value); if (passwordError) setPasswordError("") }}
            aria-invalid={!!passwordError}
            className={passwordError ? INPUT_ERR : INPUT_OK}
            disabled={loading}
          />
          {passwordError && <FieldError message={passwordError} />}
        </div>

        <Button
          type="submit"
          className="w-full h-12 rounded-full font-bold text-base mt-6 bg-primary text-primary-foreground"
          disabled={loading}
        >
          {loading ? "Logging in..." : "Log in"}
        </Button>
      </form>
    </AuthFormContainer>
  )
}
