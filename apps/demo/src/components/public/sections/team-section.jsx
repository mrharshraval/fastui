"use client"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

export function PublicTeamSection({ data }) {
    if (!data?.members?.length) return null

    return (
        <div className="my-16 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {data.members.map((member, index) => (
                <div key={index} className="flex flex-col items-center space-y-4">
                    <Avatar className="h-32 w-32 border-4 border-muted">
                        <AvatarImage src={member.image} className="object-cover" />
                        <AvatarFallback>{member.name?.[0]}</AvatarFallback>
                    </Avatar>
                    <div>
                        <h4 className="font-bold text-lg">{member.name}</h4>
                        <p className="text-sm text-muted-foreground">{member.role}</p>
                    </div>
                </div>
            ))}
        </div>
    )
}
