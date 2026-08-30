import React from "react"
import Link from "next/link"

interface AuthFormContainerProps {
  title: string
  subtitle?: string
  children: React.ReactNode
  footerText?: string
  footerLinkText?: string
  footerLinkHref?: string
  showTerms?: boolean
}

export function AuthFormContainer({
  title,
  subtitle,
  children,
  footerText,
  footerLinkText,
  footerLinkHref,
  showTerms = true,
}: AuthFormContainerProps) {
  return (
    <div className="w-full max-w-[324px] mx-auto flex flex-col items-center">
      {/* Brand Icon */}
      <div className="mb-8 flex justify-center">
        <img
          src="/assets/brand/icon/monochrome/white/filled.svg"
          alt="fastui"
          className="size-12 hidden dark:block object-contain"
        />
        <img
          src="/assets/brand/icon/monochrome/balck/filled.svg"
          alt="fastui"
          className="size-12 dark:hidden object-contain"
        />
      </div>

      {/* Title */}
      <h1 className="text-[32px] leading-tight font-bold tracking-tight text-foreground text-center mb-2">
        {title}
      </h1>

      {/* Subtitle */}
      {subtitle && (
        <p className="text-base text-muted-foreground text-center mb-8 font-medium">
          {subtitle}
        </p>
      )}

      {/* Spacing when no subtitle */}
      {!subtitle && <div className="mb-6" />}

      {children}

      {footerText && footerLinkText && footerLinkHref && (
        <div className="w-full mt-8 flex items-center justify-center gap-1.5 text-sm">
          <span className="text-muted-foreground font-medium tracking-wide">
            {footerText}
          </span>
          <Link
            href={footerLinkHref}
            className="text-foreground font-bold transition-colors hover:opacity-80"
          >
            {footerLinkText}
          </Link>
        </div>
      )}

      {showTerms && (
        <div className="w-full mt-12 text-center">
          <p className="text-xs text-muted-foreground leading-relaxed">
            By continuing, you agree to the{" "}
            <Link href="/terms" className="text-xs font-bold hover:text-foreground">
              Terms of Use
            </Link>
            {" "}and{" "}
            <Link href="/privacy" className="text-xs font-bold hover:text-foreground">
              Privacy Policy
            </Link>
            .
          </p>
        </div>
      )}
    </div>
  )
}

