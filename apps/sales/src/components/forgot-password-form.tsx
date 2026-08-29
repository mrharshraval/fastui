"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AlertCircle, CheckCircle2, Mail, ArrowLeft } from "lucide-react"
import { AuthFormContainer } from "./auth-form-container"
import { api } from "@/lib/api"
import Link from "next/link"

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

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [emailError, setEmailError] = useState("")
  const [sent, setSent] = useState(false)
  const [cooldown, setCooldown] = useState(30)
  const [resending, setResending] = useState(false)

  useEffect(() => {
    if (!sent || cooldown <= 0) return
    const timer = setInterval(() => {
      setCooldown((prev) => prev - 1)
    }, 1000)
    return () => clearInterval(timer)
  }, [sent, cooldown])

  const validateEmail = (val: string) => {
    if (!val) { setEmailError("Please enter your email address."); return false }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
      setEmailError("Please enter a valid email address.")
      return false
    }
    setEmailError("")
    return true
  }

  const handleRequest = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateEmail(email)) return
    setLoading(true)
    try {
      await api.post("/auth/password/reset/request", { email: email.trim().toLowerCase() })
      setSent(true)
      setCooldown(30)
    } catch (err: unknown) {
      setEmailError(err instanceof Error ? err.message : "Failed to send reset email")
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    if (cooldown > 0 || resending || !email) return
    setResending(true)
    try {
      await api.post("/auth/password/reset/request", { email: email.trim().toLowerCase() })
      setCooldown(30)
    } catch {
      // Ignored for UX
    } finally {
      setResending(false)
    }
  }

  if (sent) {
    return (
      <AuthFormContainer
        title="Check your email"
        subtitle={`We've sent password reset instructions to ${email}`}
        footerText="Remember your password?"
        footerLinkText="Log in"
        footerLinkHref="/login"
      >
        <div className="w-full flex flex-col gap-4 py-2">
          <p className="text-sm text-muted-foreground text-center leading-relaxed">
            Click the link in the email to reset your password. If you don't see it, check your spam or junk folder.
          </p>

          <div className="w-full flex flex-col gap-3 mt-2">
            <button
              type="button"
              onClick={handleResend}
              disabled={cooldown > 0 || resending}
              className="w-full h-12 rounded-full font-bold text-sm border border-border hover:border-foreground/40 bg-transparent text-foreground disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {cooldown > 0
                ? `Resend link in ${cooldown}s`
                : resending
                ? "Sending..."
                : "Didn't receive email? Resend"}
            </button>

            <Link
              href="/login"
              className="text-xs text-muted-foreground hover:text-foreground text-center py-2 flex items-center justify-center gap-1 font-medium"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to log in</span>
            </Link>
          </div>
        </div>
      </AuthFormContainer>
    )
  }

  return (
    <AuthFormContainer
      title="Reset password"
      subtitle="Enter your email to receive instructions to reset your password."
      footerText="Remember your password?"
      footerLinkText="Log in"
      footerLinkHref="/login"
    >
      <form onSubmit={handleRequest} className="w-full space-y-4">
        <div className="space-y-1.5 flex flex-col items-start w-full">
          <Label htmlFor="email" className="text-sm font-bold text-foreground">
            Email address
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="name@domain.com"
            value={email}
            onChange={(e) => { setEmail(e.target.value); if (emailError) validateEmail(e.target.value) }}
            onBlur={() => { if (email) validateEmail(email) }}
            aria-invalid={!!emailError}
            className={emailError ? INPUT_ERR : INPUT_OK}
            disabled={loading}
          />
          {emailError && <FieldError message={emailError} />}
        </div>

        <Button
          type="submit"
          className="w-full h-12 rounded-full font-bold text-base mt-6 bg-primary text-primary-foreground"
          disabled={loading}
        >
          {loading ? "Sending link..." : "Send reset link"}
        </Button>
      </form>
    </AuthFormContainer>
  )
}
