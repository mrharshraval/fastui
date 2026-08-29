import { Suspense } from "react"
import { VerifyOtpForm } from "@/components/verify-otp-form"

export default function VerifyPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center p-8 text-muted-foreground text-sm">Loading verification...</div>}>
      <VerifyOtpForm />
    </Suspense>
  )
}
