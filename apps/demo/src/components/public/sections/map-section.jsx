"use client"

export function PublicMapSection({ data }) {
    if (!data?.url) return null

    return (
        <div className="my-12 rounded-xl overflow-hidden shadow-sm h-[400px] bg-muted">
            <iframe
                src={data.url}
                width="100%"
                height="100%"
                style={{ border: 0 }}
                allowFullScreen
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
            />
        </div>
    )
}
