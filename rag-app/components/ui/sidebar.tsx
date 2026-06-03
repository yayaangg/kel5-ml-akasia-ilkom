"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { MessageSquarePlus, Home, Menu, X, MessageCircle, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useChat } from "@/components/chat-provider"
import { ThemeToggle } from "@/components/theme-toggle"
import Link from "next/link"
import { usePathname } from "next/navigation"

export function Sidebar() {
    const pathname = usePathname()
    const { rooms, currentRoomId, createNewRoom, switchRoom, deleteRoom } = useChat()
    const [mounted, setMounted] = React.useState(false)
    const [mobileOpen, setMobileOpen] = React.useState(false)

    // Don't show this sidebar on admin pages
    const isAdminPage = pathname?.startsWith('/admin')

    React.useEffect(() => {
        setMounted(true)
    }, [])

    // Don't render sidebar on admin pages
    if (isAdminPage) return null

    const handleNewChat = () => {
        createNewRoom()
        setMobileOpen(false)
    }

    const handleSwitchRoom = (roomId: string) => {
        switchRoom(roomId)
        setMobileOpen(false)
    }

    const handleDeleteRoom = (e: React.MouseEvent, roomId: string) => {
        e.stopPropagation()
        deleteRoom(roomId)
    }

    const SidebarContent = () => (
        <>
            <div className="p-6">
                <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400">
                    AKASIA
                </h1>
                <p className="text-xs text-slate-400 mt-1">Asisten Akademik v2.4</p>
            </div>

            <div className="flex-1 px-4 py-2 space-y-2 overflow-y-auto">
                <Link href="/chat" onClick={() => setMobileOpen(false)}>
                    <div className={cn(
                        "flex items-center gap-3 px-4 py-3 rounded-xl transition-all cursor-pointer group",
                        pathname === "/chat" ? "bg-white/10 text-white" : "text-slate-400 hover:bg-white/5 hover:text-white"
                    )}>
                        <Home className="w-5 h-5 group-hover:text-blue-400" />
                        <span className="font-medium">Chat</span>
                    </div>
                </Link>

                <div onClick={handleNewChat} className="flex items-center gap-3 px-4 py-3 rounded-xl transition-all cursor-pointer group text-slate-400 hover:bg-white/5 hover:text-white">
                    <MessageSquarePlus className="w-5 h-5 group-hover:text-green-400" />
                    <span className="font-medium">Chat Baru</span>
                </div>

                {/* Chat History */}
                {mounted && rooms.length > 0 && (
                    <div className="pt-4">
                        <p className="px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Riwayat Chat</p>
                        <div className="space-y-1">
                            {rooms.map((room) => (
                                <div
                                    key={room.id}
                                    onClick={() => handleSwitchRoom(room.id)}
                                    className={cn(
                                        "flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer group transition-all",
                                        room.id === currentRoomId
                                            ? "bg-blue-500/20 text-white border border-blue-500/30"
                                            : "text-slate-400 hover:bg-white/5 hover:text-white"
                                    )}
                                >
                                    <MessageCircle className="w-4 h-4 shrink-0" />
                                    <span className="text-sm truncate flex-1">{room.title}</span>
                                    <button
                                        onClick={(e) => handleDeleteRoom(e, room.id)}
                                        className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded transition-all"
                                    >
                                        <Trash2 className="w-3 h-3 text-red-400" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            <div className="p-4 space-y-3 border-t border-white/10">
                <ThemeToggle />
                <p className="text-xs text-slate-500 text-center">
                    AKASIA v2.4 © UHO 2025
                </p>
            </div>
        </>
    )

    return (
        <>
            {/* Mobile menu button */}
            <button
                onClick={() => setMobileOpen(!mobileOpen)}
                className="md:hidden fixed top-4 left-4 z-[60] p-2 rounded-lg bg-slate-900/90 border border-white/10 text-white"
            >
                {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>

            {/* Mobile overlay */}
            {mobileOpen && (
                <div
                    className="md:hidden fixed inset-0 bg-black/50 z-40"
                    onClick={() => setMobileOpen(false)}
                />
            )}

            {/* Mobile sidebar */}
            <motion.div
                className={cn(
                    "md:hidden fixed left-0 top-0 h-screen w-64 border-r border-white/10 bg-slate-950/95 backdrop-blur-xl z-50 flex flex-col",
                    mobileOpen ? "block" : "hidden"
                )}
                initial={{ x: -300 }}
                animate={{ x: mobileOpen ? 0 : -300 }}
            >
                <SidebarContent />
            </motion.div>

            {/* Desktop sidebar */}
            <motion.div
                className="hidden md:flex flex-col h-screen w-64 border-r border-white/10 bg-slate-950/50 backdrop-blur-xl fixed left-0 top-0 z-50"
                initial={{ x: -300 }}
                animate={{ x: 0 }}
                transition={{ type: "spring", stiffness: 100, damping: 20 }}
            >
                <SidebarContent />
            </motion.div>
        </>
    )
}
