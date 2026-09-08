"use client"

export function RichTextSection({ data }) {
    if (!data?.content) return null;

    return (
        <div
            className="prose prose-lg dark:prose-invert max-w-none mb-8"
            dangerouslySetInnerHTML={{ __html: data.content }}
        />
    )
}
