"use client"

export function PublicVideoSection({ data }) {
    if (!data?.url) return null

    // Simple embed logic
    const getEmbedUrl = (url) => {
        if (url.includes("youtube.com") || url.includes("youtu.be")) {
            const id = url.split("v=")[1]?.split("&")[0] || url.split("/").pop()
            return `https://www.youtube.com/embed/${id}`
        }
        if (url.includes("vimeo.com")) {
            const id = url.split("/").pop()
            return `https://player.vimeo.com/video/${id}`
        }
        return url
    }

    return (
        <div className="my-12 rounded-lg overflow-hidden aspect-video bg-black">
            <iframe
                src={getEmbedUrl(data.url)}
                className="w-full h-full"
                allowFullScreen
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            />
        </div>
    )
}
