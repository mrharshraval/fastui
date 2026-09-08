import { BookingForm } from "@/components/sections/booking-form"

export default function BookPage() {
    return (
        <main className="flex min-h-screen flex-col pt-24 pb-20 bg-background">
            <div className="container px-8 sm:px-4 md:px-12 space-y-12">
                {/* Header */}
                <div className="text-center max-w-3xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <div className="inline-flex items-center rounded-full bg-secondary px-3 py-1 text-sm font-medium text-secondary-foreground">
                        Schedule a Visit
                    </div>
                    <h1 className="text-4xl md:text-6xl font-bold tracking-tighter">
                        Book Your Appointment
                    </h1>
                    <p className="text-xl text-muted-foreground leading-relaxed max-w-2xl mx-auto">
                        Ready to enhance your smile? Fill out the form below and our team will get back to you within 24 hours to confirm your time.
                    </p>
                </div>

                {/* Form Container */}
                <div className="max-w-2xl mx-auto bg-card rounded-xl border shadow-sm p-6 md:p-8 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-150">
                    <BookingForm />
                </div>
            </div>
        </main>
    )
}
