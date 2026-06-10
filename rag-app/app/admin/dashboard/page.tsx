"use client"

import * as React from "react"
import { StatsCard } from "@/components/admin/stats-card"
import { AnalyticsChart } from "@/components/admin/analytics-chart"
import { FeedbackDashboard } from "@/components/admin/feedback-dashboard"
import { QueryTester } from "@/components/admin/query-tester"
import { GlassCard } from "@/components/ui/glass-card"
import { FileText, Database, Activity, Clock, AlertCircle, ThumbsUp, Beaker } from "lucide-react"

interface Document {
    id: string
    filename: string
    size_bytes: number
    uploaded_at: string
    status: string
    chunks_count: number
}

interface Stats {
    total_documents: number
    total_queries: number
    total_size_bytes: number
    vector_db_size_bytes: number
    last_query_at: string | null
}

export default function AdminPage() {
    const [documents, setDocuments] = React.useState<Document[]>([])
    const [stats, setStats] = React.useState<Stats | null>(null)
    const [loading, setLoading] = React.useState(true)
    const [error, setError] = React.useState<string | null>(null)
    const [deleteStatus, setDeleteStatus] = React.useState<{ id: string, status: 'loading' | 'success' | 'error' } | null>(null)
    const [backendOnline, setBackendOnline] = React.useState(true)

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

    const getToken = () => {
        if (typeof window === "undefined") return null
        return localStorage.getItem("admin_token")
    }

    const fetchData = async () => {
        setLoading(true)
        setError(null)

        try {
            const token = getToken()

            if (!token) {
                setError("Belum login admin")
                setBackendOnline(false)
                setLoading(false)
                return
            }

            const [docsRes, statsRes] = await Promise.all([
                fetch(`${API_URL}/api/documents`, {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }),
                fetch(`${API_URL}/api/stats`, {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                })
            ])

            if (docsRes.status === 401 || statsRes.status === 401) {
                localStorage.removeItem("admin_token")
                throw new Error("Token tidak valid / expired, silakan login ulang")
            }

            if (!docsRes.ok || !statsRes.ok) {
                throw new Error("Failed to fetch data")
            }

            const docsData = await docsRes.json()
            const statsData = await statsRes.json()

            setDocuments(docsData.documents || [])
            setStats(statsData)
            setBackendOnline(true)

        } catch (err: any) {
            setError(err.message || "Tidak dapat terhubung ke backend")
            setBackendOnline(false)
        } finally {
            setLoading(false)
        }
    }

    React.useEffect(() => {
        fetchData()
    }, [])

    const handleDelete = async (docId: string) => {
        if (!confirm("Yakin ingin menghapus dokumen ini?")) return

        setDeleteStatus({ id: docId, status: "loading" })

        try {
            const token = getToken()

            const res = await fetch(`${API_URL}/api/documents/${docId}`, {
                method: "DELETE",
                headers: {
                    Authorization: `Bearer ${token}`
                }
            })

            if (res.status === 401) {
                localStorage.removeItem("admin_token")
                throw new Error("Session habis, login ulang")
            }

            if (!res.ok) throw new Error("Delete failed")

            setDeleteStatus({ id: docId, status: "success" })

            setTimeout(() => {
                setDeleteStatus(null)
                fetchData()
            }, 1000)

        } catch (err) {
            setDeleteStatus({ id: docId, status: "error" })
            setTimeout(() => setDeleteStatus(null), 2000)
        }
    }

    const formatBytes = (bytes: number) => {
        if (!bytes) return "0 B"
        const k = 1024
        const sizes = ["B", "KB", "MB", "GB"]
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
    }

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr)
        const now = new Date()
        const diff = now.getTime() - date.getTime()
        const minutes = Math.floor(diff / 60000)
        const hours = Math.floor(diff / 3600000)
        const days = Math.floor(diff / 86400000)

        if (minutes < 1) return "Baru saja"
        if (minutes < 60) return `${minutes} menit yang lalu`
        if (hours < 24) return `${hours} jam yang lalu`
        return `${days} hari yang lalu`
    }

    return (
        <div className="p-6 lg:p-8 pb-32 space-y-8">

            {/* HEADER */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">
                        Control Center
                    </h1>
                    <p className="text-slate-400 mt-1">
                        Kelola knowledge base & monitoring sistem
                    </p>
                </div>

                <div className={`px-3 py-1 rounded-full text-sm border ${backendOnline
                    ? "text-green-400 border-green-500/30"
                    : "text-red-400 border-red-500/30"
                    }`}>
                    {backendOnline ? "System Online" : "Backend Offline"}
                </div>
            </div>

            {/* ERROR */}
            {error && (
                <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                    <AlertCircle className="w-5 h-5 text-red-400" />
                    <p className="text-red-400">{error}</p>
                    <button
                        onClick={fetchData}
                        className="ml-auto px-3 py-1 bg-red-500/20 rounded-lg"
                    >
                        Retry
                    </button>
                </div>
            )}

            {/* STATS */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

                <StatsCard
                    title="Total Dokumen"
                    value={stats?.total_documents || 0}
                    change={documents.length + " aktif"}
                    icon={FileText}
                    color="blue"
                />

                <StatsCard
                    title="Total Queries"
                    value={stats?.total_queries || 0}
                    change={stats?.last_query_at ? formatDate(stats.last_query_at) : "Belum ada"}
                    icon={Activity}
                    color="purple"
                />

                <StatsCard
                    title="Ukuran Data"
                    value={formatBytes(stats?.total_size_bytes || 0)}
                    change="Dokumen"
                    icon={Clock}
                    color="cyan"
                />

                <StatsCard
                    title="Vector DB"
                    value={formatBytes(stats?.vector_db_size_bytes || 0)}
                    change="FAISS"
                    icon={Database}
                    color="green"
                />

            </div>

            {/* ANALYTICS */}
            <div>
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <Activity className="w-5 h-5 text-purple-400" />
                    Analytics
                </h2>
                <AnalyticsChart />
            </div>

            {/* FEEDBACK */}
            <div>
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <ThumbsUp className="w-5 h-5 text-emerald-400" />
                    Feedback
                </h2>
                <FeedbackDashboard />
            </div>

            {/* QA TEST */}
            <div>
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <Beaker className="w-5 h-5 text-cyan-400" />
                    QA Testing
                </h2>

                <GlassCard>
                    <QueryTester />
                </GlassCard>
            </div>

        </div>
    )
}