"use client"

export function PublicAudioSection({ data }) {
    if (!data?.url) return null

    return (
        <div className="my-8">
            <audio controls className="w-full">
                <source src={data.url} />
                Your browser does not support the audio tag.
            </audio>
        </div>
    )
}
