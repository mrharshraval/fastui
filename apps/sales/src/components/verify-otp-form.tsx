"use client"

import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp"
import { AlertCircle, CheckCircle2, ArrowLeft } from "lucide-react"
import { AuthFormContainer } from "./auth-form-container"
import { api } from "@/lib/api"

function FieldError({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-1.5 mt-1 text-destructive">
      <AlertCircle className="size-4 mt-0.5 shrink-0" />
      <p className="text-sm leading-tight font-medium">{message}</p>
    </div>
  )
}

interface VerifyOtpFormProps {
  initialEmail?: string
  onSuccess?: () => void
  onChangeEmail?: () => void
}

export function VerifyOtpForm({
  initialEmail,
  onSuccess,
  onChangeEmail,
}: VerifyOtpFormProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const email = initialEmail || searchParams.get("email") || ""
  
  const [otp, setOtp] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [resendCooldown, setResendCooldown] = useState(30)
  const [resending, setResending] = useState(false)
  const [resendSuccess, setResendSuccess] = useState(false)

  // Countdown timer for resend
  useEffect(() => {
    if (resendCooldown <= 0) return
    const timer = setInterval(() => {
      setResendCooldown((prev) => prev - 1)
    }, 1000)
    return () => clearInterval(timer)
  }, [resendCooldown])

  const handleVerify = async (codeToVerify?: string) => {
    const code = codeToVerify || otp
    if (!code || code.length !== 6) {
      setError("Please enter the complete 6-digit code.")
      return
    }

    setLoading(true)
    setError("")

    try {
      const res = await api.post<{ user?: { id: number; email: string; role: string } }>("/auth/verify", {
        email: email.trim().toLowerCase(),
        otp: code,
      })

      if (res?.user) {
        localStorage.setItem("fastui_user", JSON.stringify(res.user))
      } else if (email) {
        localStorage.setItem("fastui_user", JSON.stringify({ email: email.trim().toLowerCase() }))
      }

      if (onSuccess) {
        onSuccess()
      } else {
        router.push("/")
        router.refresh()
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Verification failed. Please check the code and try again."
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    if (resendCooldown > 0 || resending || !email) return
    setResending(true)
    setError("")
    setResendSuccess(false)

    try {
      await api.post("/auth/register", {
        email: email.trim().toLowerCase(),
        password: "TempPasswordResend123!",
      })
      setResendSuccess(true)
      setResendCooldown(30)
    } catch (err: unknown) {
      setResendSuccess(true)
      setResendCooldown(30)
    } finally {
      setResending(false)
    }
  }

  return (
    <AuthFormContainer
      title="Check your email"
      subtitle={email ? `We've sent a 6-digit code to ${email}` : "Enter the 6-digit verification code sent to your email."}
      footerText="Already verified?"
      footerLinkText="Log in"
      footerLinkHref="/login"
    >
      <div className="w-full flex flex-col items-center">
        {/* OTP Input */}
        <div className="my-2 flex justify-center w-full">
          <InputOTP
            maxLength={6}
            value={otp}
            onChange={(value) => {
              setOtp(value)
              if (error) setError("")
              if (value.length === 6) {
                handleVerify(value)
              }
            }}
            disabled={loading}
          >
            <InputOTPGroup className="gap-2 sm:gap-2.5">
              <InputOTPSlot index={0} />
              <InputOTPSlot index={1} />
              <InputOTPSlot index={2} />
              <InputOTPSlot index={3} />
              <InputOTPSlot index={4} />
              <InputOTPSlot index={5} />
            </InputOTPGroup>
          </InputOTP>
        </div>

        {error && <FieldError message={error} />}

        {resendSuccess && (
          <div className="flex items-center gap-1.5 mt-3 text-emerald-400 text-sm font-medium">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>A new code has been sent to your email.</span>
          </div>
        )}

        {/* Action Button */}
        <Button
          type="button"
          onClick={() => handleVerify()}
          className="w-full h-12 rounded-full font-bold text-base mt-6 bg-primary text-primary-foreground"
          disabled={loading || otp.length !== 6}
        >
          {loading ? "Verifying..." : "Verify & Continue"}
        </Button>

        {/* Resend & Back Actions */}
        <div className="w-full mt-6 flex flex-col items-center gap-3">
          <button
            type="button"
            onClick={handleResend}
            disabled={resendCooldown > 0 || resending}
            className="text-sm text-muted-foreground hover:text-foreground disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {resendCooldown > 0
              ? `Resend code in ${resendCooldown}s`
              : resending
              ? "Sending new code..."
              : "Didn't receive code? Resend"}
          </button>

          {onChangeEmail && (
            <button
              type="button"
              onClick={onChangeEmail}
              className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 font-medium mt-1"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Change email address</span>
            </button>
          )}
        </div>
      </div>
    </AuthFormContainer>
  )
}