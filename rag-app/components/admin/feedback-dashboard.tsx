"use client"

/**
 * FeedbackDashboard Component - AKASIA v2.3
 * Menampilkan statistik feedback dan recent ratings
 */

import * as React from "react"
import { motion } from "framer-motion"
import { ThumbsUp, ThumbsDown, TrendingUp, MessageSquare, Clock } from "lucide-react"

interface FeedbackStats {
    thumbs_up: number
    thumbs_down: number
    total: number
    satisfaction_rate: number
    recent_feedback: Array<{
        query: string
        response: string
        rating: string
        confidence?: number
        timestamp: string
    }>
}

export function FeedbackDashboard() {
    const [stats, setStats] = React.useState<FeedbackStats | null>(null)
    const [loading, setLoading] = React.useState(true)

    React.useEffect(() => {
        fetchStats()
        // Refresh every 30 seconds
        const interval = setInterval(fetchStats, 30000)
        return () => clearInterval(interval)
    }, [])

    const fetchStats = async () => {
        try {
            const res = await fetch("http://localhost:8000/api/feedback/stats")
            if (res.ok) {
                const data = await res.json()
                setStats(data)
            }
        } catch (error) {
            console.error("Failed to fetch feedback stats:", error)
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-6">
                <div className="animate-pulse space-y-4">
                    <div className="h-6 bg-slate-700 rounded w-1/3"></div>
                    <div className="h-24 bg-slate-700/50 rounded"></div>
                </div>
            </div>
        )
    }

    if (!stats) {
        return (
            <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-6 text-center text-slate-400">
                <MessageSquare className="w-12 h-12 mx-auto mb-3 text-slate-600" />
                <p>Belum ada data feedback</p>
            </div>
        )
    }

    const getSatisfactionColor = (rate: number) => {
        if (rate >= 80) return "text-emerald-400"
        if (rate >= 50) return "text-amber-400"
        return "text-red-400"
    }

    const getSatisfactionBg = (rate: number) => {
        if (rate >= 80) return "from-emerald-500/20 to-emerald-500/5"
        if (rate >= 50) return "from-amber-500/20 to-amber-500/5"
        return "from-red-500/20 to-red-500/5"
    }

    return (
        <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Satisfaction Rate */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`bg-gradient-to-br ${getSatisfactionBg(stats.satisfaction_rate)} border border-slate-700/50 rounded-xl p-5`}
                >
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm text-slate-400">Satisfaction Rate</span>
                        <TrendingUp className={`w-5 h-5 ${getSatisfactionColor(stats.satisfaction_rate)}`} />
                    </div>
                    <div className={`text-3xl font-bold ${getSatisfactionColor(stats.satisfaction_rate)}`}>
                        {stats.satisfaction_rate}%
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                        dari {stats.total} feedback
                    </div>
                </motion.div>

                {/* Thumbs Up */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 border border-emerald-500/20 rounded-xl p-5"
                >
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm text-slate-400">Positif</span>
                        <ThumbsUp className="w-5 h-5 text-emerald-400" />
                    </div>
                    <div className="text-3xl font-bold text-emerald-400">
                        {stats.thumbs_up}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                        jawaban membantu
                    </div>
                </motion.div>

                {/* Thumbs Down */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="bg-gradient-to-br from-red-500/10 to-red-500/5 border border-red-500/20 rounded-xl p-5"
                >
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm text-slate-400">Negatif</span>
                        <ThumbsDown className="w-5 h-5 text-red-400" />
                    </div>
                    <div className="text-3xl font-bold text-red-400">
                        {stats.thumbs_down}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                        perlu perbaikan
                    </div>
                </motion.div>
            </div>

            {/* Recent Feedback */}
            {stats.recent_feedback && stats.recent_feedback.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-5"
                >
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Clock className="w-5 h-5 text-blue-400" />
                        Feedback Terbaru
                    </h3>
                    <div className="space-y-3 max-h-64 overflow-y-auto">
                        {stats.recent_feedback.map((fb, i) => (
                            <div
                                key={i}
                                className={`p-3 rounded-lg border ${fb.rating === "up"
                                        ? "bg-emerald-500/5 border-emerald-500/20"
                                        : "bg-red-500/5 border-red-500/20"
                                    }`}
                            >
                                <div className="flex items-start justify-between gap-3">
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm text-slate-300 font-medium truncate">
                                            {fb.query}
                                        </p>
                                        <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                                            {fb.response}
                                        </p>
                                    </div>
                                    <div className="flex items-center gap-2 shrink-0">
                                        {fb.confidence && (
                                            <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-300">
                                                {fb.confidence}%
                                            </span>
                                        )}
                                        {fb.rating === "up" ? (
                                            <ThumbsUp className="w-4 h-4 text-emerald-400" />
                                        ) : (
                                            <ThumbsDown className="w-4 h-4 text-red-400" />
                                        )}
                                    </div>
                                </div>
                                <div className="text-xs text-slate-600 mt-2">
                                    {new Date(fb.timestamp).toLocaleString("id-ID")}
                                </div>
                            </div>
                        ))}
                    </div>
                </motion.div>
            )}
        </div>
    )
}
