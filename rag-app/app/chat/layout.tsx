"use client"

import * as React from "react"
import { Sidebar } from "@/components/ui/sidebar"

export default function ChatLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <>
            <Sidebar />
            <main className="md:pl-64 min-h-screen relative z-10">
                {children}
            </main>
        </>
    )
}
