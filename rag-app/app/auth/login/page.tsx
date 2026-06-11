"use client"

import React from "react"
import { motion } from "framer-motion"
import { Lock, User, Sparkles } from "lucide-react"

export default function AdminLoginPage() {
    const [username, setUsername] = React.useState("")
    const [password, setPassword] = React.useState("")
    const [loading, setLoading] = React.useState(false)
    const [error, setError] = React.useState("")

    const handleLogin = async () => {
        setLoading(true)
        setError("")

        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
            const res = await fetch(`${API_URL}/api/admin/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            })

            const data = await res.json()

            if (!res.ok) throw new Error(data.detail || "Login gagal")

            localStorage.setItem("admin_token", data.token)

            window.location.href = "/admin/dashboard"
        } catch (err: any) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#070A12] relative overflow-hidden">

            {/* Background glow */}
            <div className="absolute w-[500px] h-[500px] bg-purple-600/20 blur-[120px] rounded-full top-[-100px] left-[-100px]" />
            <div className="absolute w-[400px] h-[400px] bg-blue-600/20 blur-[120px] rounded-full bottom-[-100px] right-[-100px]" />

            {/* Login Card */}
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-[380px] p-8 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl shadow-2xl"
            >
                {/* Header */}
                <div className="text-center mb-6">
                    <div className="flex justify-center mb-3">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                            <Lock className="w-6 h-6 text-white" />
                        </div>
                    </div>

                    <h1 className="text-xl font-bold text-white">
                        Admin Login
                    </h1>
                    <p className="text-slate-400 text-sm">
                        AKASIA Control Panel
                    </p>
                </div>

                {/* Input Username */}
                <div className="mb-3">
                    <label className="text-xs text-slate-400">Username</label>
                    <div className="flex items-center gap-2 mt-1 px-3 py-2 rounded-lg bg-white/5 border border-white/10">
                        <User className="w-4 h-4 text-slate-400" />
                        <input
                            className="bg-transparent outline-none text-white w-full text-sm"
                            placeholder="admin"
                            onChange={(e) => setUsername(e.target.value)}
                        />
                    </div>
                </div>

                {/* Input Password */}
                <div className="mb-4">
                    <label className="text-xs text-slate-400">Password</label>
                    <div className="flex items-center gap-2 mt-1 px-3 py-2 rounded-lg bg-white/5 border border-white/10">
                        <Lock className="w-4 h-4 text-slate-400" />
                        <input
                            type="password"
                            className="bg-transparent outline-none text-white w-full text-sm"
                            placeholder="••••••••"
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>
                </div>

                {error && (
                    <p className="text-red-400 text-xs mb-3">{error}</p>
                )}

                {/* Button */}
                <button
                    onClick={handleLogin}
                    disabled={loading}
                    className="w-full py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium flex items-center justify-center gap-2 hover:opacity-90 transition"
                >
                    {loading ? (
                        "Loading..."
                    ) : (
                        <>
                            <Sparkles className="w-4 h-4" />
                            Login
                        </>
                    )}
                </button>

                {/* footer */}
                <p className="text-center text-xs text-slate-500 mt-4">
                    Secure access only for admin
                </p>
            </motion.div>
        </div>
    )
}