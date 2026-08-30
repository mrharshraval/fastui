"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AlertCircle, CheckCircle2, Mail } from "lucide-react"
import { AuthFormContainer } from "./auth-form-container"
import { api } from "@/lib/api"
import Link from "next/link"

const BASE_INPUT = "w-full bg-transparent rounded-full h-12 px-4 text-sm placeholder:text-muted-foreground border transition-all outline-none"
const INPUT_OK = `${BASE_INPUT} border-border dark:border-white/20 text-foreground hover:border-foreground/60 focus:border-foreground focus:ring-1 focus:ring-foreground/20`
const INPUT_ERR = `${BASE_INPUT} border-destructive text-foreground focus:border-destructive hover:border-destructive ring-1 ring-destructive/30`

function FieldError({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-1.5 mt-1 text-destructive">
      <AlertCircle className="size-3.5 mt-0.5 shrink-0" />
      <p className="text-xs leading-tight font-medium">{message}</p>
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
    if (!val) { setEmailError("Enter your email."); return false }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
      setEmailError("Enter a valid email address.")
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
        showTerms={false}
      >
        <div className="w-full flex flex-col gap-3 py-2">
          <button
            type="button"
            onClick={handleResend}
            disabled={cooldown > 0 || resending}
            className="w-full h-12 rounded-full font-semibold text-sm border border-border dark:border-white/20 hover:border-foreground/40 bg-transparent text-foreground disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {cooldown > 0
              ? `Resend link in ${cooldown}s`
              : resending
              ? "Sending..."
              : "Didn't receive email? Resend"}
          </button>
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
      showTerms={false}
    >
      <form onSubmit={handleRequest} className="w-full space-y-4">
        <div className="space-y-1.5 flex flex-col items-start w-full">
          <Label htmlFor="email" className="text-sm font-bold text-foreground tracking-tight">
            Email
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
          className="w-full h-12 rounded-full font-semibold text-sm mt-6 cursor-pointer bg-primary text-primary-foreground"
        >
          Send reset link
        </Button>
      </form>
    </AuthFormContainer>
  )
}
