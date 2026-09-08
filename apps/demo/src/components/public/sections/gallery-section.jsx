"use client"

export function PublicGallerySection({ data }) {
    if (!data?.images?.length) return null

    return (
        <div className="my-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.images.map((img, index) => (
                <figure key={index} className="relative group overflow-hidden rounded-lg">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                        src={img.url}
                        alt={img.caption || "Gallery image"}
                        className="w-full h-full object-cover aspect-square hover:scale-105 transition-transform duration-500"
                    />
                    {img.caption && (
                        <figcaption className="absolute bottom-0 left-0 right-0 p-2 bg-black/60 text-white text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                            {img.caption}
                        </figcaption>
                    )}
                </figure>
            ))}
        </div>
    )
}
