import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function NotFound() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center px-4 text-center">
      <div className="mx-auto max-w-md space-y-4">
        <p className="text-sm font-semibold tracking-wide text-muted-foreground uppercase">
          404
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
          Page Not Found
        </h1>
        <p className="text-sm text-muted-foreground">
          The page you requested does not exist or the link has expired.
        </p>
        <div className="pt-4 flex justify-center">
          <Link href="/">
            <Button size="lg" className="rounded-full px-6 font-medium">
              Home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
