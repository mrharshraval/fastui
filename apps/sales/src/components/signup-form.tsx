"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AlertCircle } from "lucide-react"
import { AuthFormContainer } from "./auth-form-container"
import { api } from "@/lib/api"

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

import { VerifyOtpForm } from "./verify-otp-form"

export function SignupForm() {
  const router = useRouter()
  const [step, setStep] = useState<"form" | "otp">("form")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [emailError, setEmailError] = useState("")
  const [passwordError, setPasswordError] = useState("")

  const validateEmail = (val: string) => {
    if (!val) { setEmailError("Enter your email."); return false }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
      setEmailError("Enter a valid email address.")
      return false
    }
    setEmailError("")
    return true
  }

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault()
    let valid = validateEmail(email)
    if (!password) { setPasswordError("Enter a password."); valid = false } else setPasswordError("")
    if (!valid) return
    setLoading(true)
    try {
      await api.post("/auth/register", { email, password })
      // Smoothly transition to OTP verification step
      setStep("otp")
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Registration failed"
      if (msg.toLowerCase().includes("email")) setEmailError(msg)
      else setPasswordError(msg)
    } finally {
      setLoading(false)
    }
  }

  if (step === "otp") {
    return (
      <VerifyOtpForm
        initialEmail={email}
        onChangeEmail={() => setStep("form")}
        onSuccess={() => router.push("/")}
      />
    )
  }

  return (
    <AuthFormContainer
      title="Sign up"
      footerText="Already have an account?"
      footerLinkText="Log in"
      footerLinkHref="/login"
    >
      <form onSubmit={handleSignup} className="w-full space-y-4">
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

        <div className="space-y-1.5 flex flex-col items-start w-full">
          <Label htmlFor="password" className="text-sm font-bold text-foreground tracking-tight">
            Password
          </Label>
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
          className="w-full h-12 rounded-full font-semibold text-sm mt-6 cursor-pointer bg-primary text-primary-foreground"
        >
          Sign up
        </Button>
      </form>
    </AuthFormContainer>
  )
}
