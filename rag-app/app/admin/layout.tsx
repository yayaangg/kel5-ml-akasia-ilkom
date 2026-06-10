"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { motion } from "framer-motion"
import {
    LayoutDashboard,
    FileText,
    Settings,
    ArrowLeft,
    Menu,
    X,
    LogOut
} from "lucide-react"
import { cn } from "@/lib/utils"

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const pathname = usePathname()
    const router = useRouter()
    const [mobileOpen, setMobileOpen] = React.useState(false)

    const navItems = [
        { href: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
        { href: "/admin/documents", label: "Dokumen", icon: FileText },
        { href: "/admin/settings", label: "Pengaturan", icon: Settings },
    ]

    // ========================
    // AUTH GUARD
    // ========================
    React.useEffect(() => {
        const token = localStorage.getItem("admin_token")

        if (!token) {
            router.replace("/auth/login")
        }
    }, [router])

    const handleLogout = () => {
        localStorage.removeItem("admin_token")
        router.replace("/auth/login")
    }

    const SidebarContent = () => (
        <>
            <div className="p-6">
                <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">
                    Admin Panel
                </h1>
                <p className="text-xs text-slate-400 mt-1">
                    AKASIA Control Center
                </p>
            </div>

            {/* NAVIGATION */}
            <div className="flex-1 px-4 py-2 space-y-2">
                {navItems.map((item) => (
                    <Link key={item.href} href={item.href} onClick={() => setMobileOpen(false)}>
                        <div
                            className={cn(
                                "flex items-center gap-3 px-4 py-3 rounded-xl transition-all cursor-pointer group",
                                pathname === item.href
                                    ? "bg-purple-500/20 text-white border border-purple-500/30"
                                    : "text-slate-400 hover:bg-white/5 hover:text-white"
                            )}
                        >
                            <item.icon className="w-5 h-5" />
                            <span className="font-medium">{item.label}</span>
                        </div>
                    </Link>
                ))}
            </div>

            {/* BACK TO CHAT */}
            <div className="p-4 border-t border-white/10">
                <Link href="/chat" onClick={() => setMobileOpen(false)}>
                    <div className="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 hover:bg-white/5 hover:text-white cursor-pointer transition-all">
                        <ArrowLeft className="w-5 h-5" />
                        <span className="font-medium">Kembali ke Chat</span>
                    </div>
                </Link>

                {/* LOGOUT */}
                <div
                    onClick={handleLogout}
                    className="flex items-center gap-3 px-4 py-3 mt-2 rounded-xl text-red-400 hover:bg-red-500/10 cursor-pointer transition-all"
                >
                    <LogOut className="w-5 h-5" />
                    <span className="font-medium">Logout</span>
                </div>
            </div>
        </>
    )

    return (
        <div className="min-h-screen bg-slate-950 text-white">

            {/* MOBILE BUTTON */}
            <button
                onClick={() => setMobileOpen(!mobileOpen)}
                className="md:hidden fixed top-4 left-4 z-[60] p-2 rounded-lg bg-slate-900/90 border border-white/10 text-white"
            >
                {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>

            {/* MOBILE OVERLAY */}
            {mobileOpen && (
                <div
                    className="md:hidden fixed inset-0 bg-black/50 z-40"
                    onClick={() => setMobileOpen(false)}
                />
            )}

            {/* MOBILE SIDEBAR */}
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

            {/* DESKTOP SIDEBAR */}
            <motion.div
                className="hidden md:flex flex-col h-screen w-64 border-r border-white/10 bg-slate-950/50 backdrop-blur-xl fixed left-0 top-0 z-50"
                initial={{ x: -300 }}
                animate={{ x: 0 }}
                transition={{ type: "spring", stiffness: 100, damping: 20 }}
            >
                <SidebarContent />
            </motion.div>

            {/* MAIN CONTENT */}
            <div className="md:pl-64 min-h-screen relative z-10">
                {children}
            </div>

        </div>
    )
}