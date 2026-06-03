"use client"

/**
 * AnalyticsChart Component - AKASIA v2.0
 * Chart analitik dengan data real-time dari backend
 */

import * as React from "react"
import { motion } from "framer-motion"
import { GlassCard } from "@/components/ui/glass-card"
import {
    AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, PieChart, Pie, Cell
} from "recharts"
import { TrendingUp, Clock, MessageSquare, RefreshCw } from "lucide-react"

interface Analytics {
    hourly_stats: Array<{ time: string; queries: number }>
    daily_stats: Array<{ day: string; date: string; queries: number }>
    popular_topics: Array<{ topic: string; count: number; percentage: number }>
    recent_queries: Array<{ query: string; timestamp: string }>
    total_queries_today: number
    total_queries_week: number
}

const COLORS = ['#8b5cf6', '#06b6d4', '#3b82f6', '#ec4899', '#10b981', '#f59e0b', '#6366f1', '#84cc16']

export function AnalyticsChart() {
    const [analytics, setAnalytics] = React.useState<Analytics | null>(null)
    const [loading, setLoading] = React.useState(true)
    const [activeTab, setActiveTab] = React.useState<'hourly' | 'daily'>('hourly')

    const fetchAnalytics = async () => {
        setLoading(true)
        try {
            const res = await fetch('http://localhost:8000/api/analytics')
            if (res.ok) {
                const data = await res.json()
                setAnalytics(data)
            }
        } catch (err) {
            console.error('Failed to fetch analytics:', err)
        } finally {
            setLoading(false)
        }
    }

    React.useEffect(() => {
        fetchAnalytics()
        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchAnalytics, 30000)
        return () => clearInterval(interval)
    }, [])

    const formatTime = (timestamp: string) => {
        if (!timestamp) return ''
        const date = new Date(timestamp)
        const now = new Date()
        const diff = now.getTime() - date.getTime()
        const minutes = Math.floor(diff / 60000)
        if (minutes < 1) return 'Baru saja'
        if (minutes < 60) return `${minutes}m lalu`
        const hours = Math.floor(diff / 3600000)
        if (hours < 24) return `${hours}j lalu`
        return date.toLocaleDateString('id-ID')
    }

    if (loading && !analytics) {
        return (
            <GlassCard className="h-[500px] flex items-center justify-center">
                <RefreshCw className="w-8 h-8 text-purple-400 animate-spin" />
            </GlassCard>
        )
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
        >
            {/* Activity Chart */}
            <GlassCard className="p-6">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h3 className="text-lg font-semibold text-white">Query Activity</h3>
                        <p className="text-sm text-slate-400">
                            {analytics?.total_queries_today || 0} hari ini • {analytics?.total_queries_week || 0} minggu ini
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setActiveTab('hourly')}
                            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${activeTab === 'hourly'
                                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                                    : 'text-slate-400 hover:text-white'
                                }`}
                        >
                            24 Jam
                        </button>
                        <button
                            onClick={() => setActiveTab('daily')}
                            className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${activeTab === 'daily'
                                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                                    : 'text-slate-400 hover:text-white'
                                }`}
                        >
                            7 Hari
                        </button>
                    </div>
                </div>

                <div className="h-[200px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        {activeTab === 'hourly' ? (
                            <AreaChart data={analytics?.hourly_stats || []}>
                                <defs>
                                    <linearGradient id="colorQueries" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                                <XAxis
                                    dataKey="time"
                                    stroke="#94a3b8"
                                    fontSize={11}
                                    tickLine={false}
                                    axisLine={false}
                                    interval={3}
                                />
                                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: "#1e293b",
                                        border: "1px solid rgba(139, 92, 246, 0.3)",
                                        borderRadius: "8px",
                                        boxShadow: "0 10px 40px rgba(0,0,0,0.3)"
                                    }}
                                    itemStyle={{ color: "#a78bfa" }}
                                    labelStyle={{ color: "#fff" }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="queries"
                                    stroke="#8b5cf6"
                                    strokeWidth={2}
                                    fillOpacity={1}
                                    fill="url(#colorQueries)"
                                    name="Queries"
                                />
                            </AreaChart>
                        ) : (
                            <BarChart data={analytics?.daily_stats || []}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                                <XAxis
                                    dataKey="day"
                                    stroke="#94a3b8"
                                    fontSize={11}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: "#1e293b",
                                        border: "1px solid rgba(6, 182, 212, 0.3)",
                                        borderRadius: "8px"
                                    }}
                                    itemStyle={{ color: "#22d3ee" }}
                                    labelStyle={{ color: "#fff" }}
                                />
                                <Bar dataKey="queries" fill="#06b6d4" radius={[4, 4, 0, 0]} name="Queries" />
                            </BarChart>
                        )}
                    </ResponsiveContainer>
                </div>
            </GlassCard>

            {/* Popular Topics & Recent Queries */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Popular Topics */}
                <GlassCard className="p-6">
                    <div className="flex items-center gap-2 mb-4">
                        <TrendingUp className="w-5 h-5 text-purple-400" />
                        <h3 className="text-lg font-semibold text-white">Topik Populer</h3>
                    </div>

                    {analytics?.popular_topics && analytics.popular_topics.length > 0 ? (
                        <div className="space-y-3">
                            {analytics.popular_topics.slice(0, 6).map((topic, i) => (
                                <motion.div
                                    key={topic.topic}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: i * 0.1 }}
                                    className="flex items-center gap-3"
                                >
                                    <div
                                        className="w-3 h-3 rounded-full"
                                        style={{ backgroundColor: COLORS[i % COLORS.length] }}
                                    />
                                    <span className="flex-1 text-sm text-slate-300">{topic.topic}</span>
                                    <span className="text-xs text-slate-500">{topic.count}x</span>
                                    <div className="w-20 h-2 bg-slate-700 rounded-full overflow-hidden">
                                        <motion.div
                                            className="h-full rounded-full"
                                            style={{ backgroundColor: COLORS[i % COLORS.length] }}
                                            initial={{ width: 0 }}
                                            animate={{ width: `${topic.percentage}%` }}
                                            transition={{ delay: i * 0.1 + 0.2, duration: 0.5 }}
                                        />
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-slate-500 text-sm text-center py-8">Belum ada data topik</p>
                    )}
                </GlassCard>

                {/* Recent Queries */}
                <GlassCard className="p-6">
                    <div className="flex items-center gap-2 mb-4">
                        <MessageSquare className="w-5 h-5 text-cyan-400" />
                        <h3 className="text-lg font-semibold text-white">Query Terbaru</h3>
                    </div>

                    {analytics?.recent_queries && analytics.recent_queries.length > 0 ? (
                        <div className="space-y-2 max-h-[250px] overflow-y-auto scrollbar-hide">
                            {analytics.recent_queries.map((q, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.05 }}
                                    className="flex items-start gap-3 p-3 rounded-lg bg-slate-800/30 hover:bg-slate-800/50 transition-colors"
                                >
                                    <Clock className="w-4 h-4 text-slate-500 mt-0.5 shrink-0" />
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm text-slate-300 truncate">{q.query}</p>
                                        <p className="text-xs text-slate-500">{formatTime(q.timestamp)}</p>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-slate-500 text-sm text-center py-8">Belum ada query</p>
                    )}
                </GlassCard>
            </div>
        </motion.div>
    )
}