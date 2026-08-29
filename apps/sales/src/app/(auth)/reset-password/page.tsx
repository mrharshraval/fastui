import { Suspense } from "react"
import { ResetPasswordForm } from "@/components/reset-password-form"

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center p-8 text-muted-foreground text-sm">Loading reset form...</div>}>
      <ResetPasswordForm />
    </Suspense>
  )
}
