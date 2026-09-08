"use client"

export function HeroModern({ data }) {
    if (!data) return null;

    const alignment = data.align || 'center'
    const textAlign = alignment === 'left' ? 'text-left' : alignment === 'right' ? 'text-right' : 'text-center'
    const itemsAlign = alignment === 'left' ? 'items-start' : alignment === 'right' ? 'items-end' : 'items-center'

    return (
        <div className="relative h-[400px] md:h-[500px] w-full flex items-center justify-center overflow-hidden bg-zinc-900 text-white mb-8 rounded-xl">
            {data.image && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                    src={data.image}
                    alt="Hero"
                    className="absolute inset-0 w-full h-full object-cover opacity-50"
                />
            )}
            <div className={`relative z-10 max-w-3xl px-6 space-y-4 flex flex-col ${textAlign} ${itemsAlign}`}>
                {data.title && (
                    <h1 className="text-4xl md:text-6xl font-bold tracking-tighter leading-tight">
                        {data.title}
                    </h1>
                )}
                {data.subtitle && (
                    <p className="text-lg md:text-xl text-zinc-200 leading-relaxed">
                        {data.subtitle}
                    </p>
                )}
            </div>
        </div>
    )
}
