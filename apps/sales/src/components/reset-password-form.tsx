"use client"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AlertCircle, CheckCircle2 } from "lucide-react"
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

export function ResetPasswordForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get("token") || ""

  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [passwordError, setPasswordError] = useState("")
  const [confirmError, setConfirmError] = useState("")
  const [generalError, setGeneralError] = useState("")
  const [success, setSuccess] = useState(false)

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault()
    setGeneralError("")

    if (!token) {
      setGeneralError("Reset token is missing or invalid. Please request a new reset link.")
      return
    }

    let valid = true
    if (!password || password.length < 8) {
      setPasswordError("Password must be at least 8 characters long.")
      valid = false
    } else {
      setPasswordError("")
    }

    if (password !== confirmPassword) {
      setConfirmError("Passwords do not match.")
      valid = false
    } else {
      setConfirmError("")
    }

    if (!valid) return

    setLoading(true)
    try {
      await api.post("/auth/password/reset/confirm", {
        token,
        new_password: password,
      })
      setSuccess(true)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to reset password"
      setGeneralError(msg)
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <AuthFormContainer
        title="Password updated"
        subtitle="Your password has been reset successfully."
        footerText="Ready to log in?"
        footerLinkText="Log in"
        footerLinkHref="/login"
      >
        <div className="w-full flex flex-col gap-4 py-2">
          <p className="text-sm text-muted-foreground text-center">
            You can now use your new password to sign in to your account.
          </p>

          <Button
            type="button"
            onClick={() => router.push("/login")}
            className="w-full h-12 rounded-full font-bold text-base bg-primary text-primary-foreground mt-2"
          >
            Continue to log in
          </Button>
        </div>
      </AuthFormContainer>
    )
  }

  if (!token) {
    return (
      <AuthFormContainer
        title="Invalid link"
        subtitle="This password reset link is invalid or has expired."
        footerText="Need help?"
        footerLinkText="Request new link"
        footerLinkHref="/forgot-password"
      >
        <div className="w-full flex flex-col gap-4 py-2">
          <p className="text-sm text-muted-foreground text-center leading-relaxed">
            Please request a new password reset link from the login page.
          </p>

          <Button
            type="button"
            onClick={() => router.push("/forgot-password")}
            className="w-full h-12 rounded-full font-bold text-base bg-primary text-primary-foreground mt-2"
          >
            Request new reset link
          </Button>
        </div>
      </AuthFormContainer>
    )
  }

  return (
    <AuthFormContainer
      title="Create new password"
      subtitle="Enter a secure new password for your fastui account."
      footerText="Remembered your password?"
      footerLinkText="Log in"
      footerLinkHref="/login"
    >
      <form onSubmit={handleReset} className="w-full space-y-4">
        {generalError && (
          <div className="p-3 rounded-2xl bg-destructive/10 border border-destructive/20 text-destructive text-sm font-medium flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{generalError}</span>
          </div>
        )}

        <div className="space-y-1.5 flex flex-col items-start w-full">
          <Label htmlFor="password" className="text-sm font-bold text-foreground">
            New password
          </Label>
          <Input
            id="password"
            type="password"
            placeholder="At least 8 characters"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value)
              if (passwordError) setPasswordError("")
            }}
            aria-invalid={!!passwordError}
            className={passwordError ? INPUT_ERR : INPUT_OK}
            disabled={loading}
          />
          {passwordError && <FieldError message={passwordError} />}
        </div>

        <div className="space-y-1.5 flex flex-col items-start w-full">
          <Label htmlFor="confirmPassword" className="text-sm font-bold text-foreground">
            Confirm new password
          </Label>
          <Input
            id="confirmPassword"
            type="password"
            placeholder="Confirm new password"
            value={confirmPassword}
            onChange={(e) => {
              setConfirmPassword(e.target.value)
              if (confirmError) setConfirmError("")
            }}
            aria-invalid={!!confirmError}
            className={confirmError ? INPUT_ERR : INPUT_OK}
            disabled={loading}
          />
          {confirmError && <FieldError message={confirmError} />}
        </div>

        <Button
          type="submit"
          className="w-full h-12 rounded-full font-bold text-base mt-6 bg-primary text-primary-foreground"
          disabled={loading}
        >
          {loading ? "Updating password..." : "Update password"}
        </Button>
      </form>
    </AuthFormContainer>
  )
}