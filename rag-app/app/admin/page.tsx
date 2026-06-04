"use client"

import * as React from "react"
import { StatsCard } from "@/components/admin/stats-card"
import { AnalyticsChart } from "@/components/admin/analytics-chart"
import { FeedbackDashboard } from "@/components/admin/feedback-dashboard"
import { QueryTester } from "@/components/admin/query-tester"
import { GlassCard } from "@/components/ui/glass-card"
import { FileText, Database, Activity, Clock, RefreshCw, AlertCircle, ThumbsUp, Beaker } from "lucide-react"

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

    const fetchData = async () => {
        setLoading(true)
        setError(null)
        try {
            const [docsRes, statsRes] = await Promise.all([
                fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/documents`),
                fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/stats`)
            ])

            if (!docsRes.ok || !statsRes.ok) {
                throw new Error('Failed to fetch data')
            }

            const docsData = await docsRes.json()
            const statsData = await statsRes.json()

            setDocuments(docsData.documents || [])
            setStats(statsData)
            setBackendOnline(true)
        } catch (err) {
            setError('Tidak dapat terhubung ke backend. Pastikan Python API berjalan di port 8000.')
            setBackendOnline(false)
        } finally {
            setLoading(false)
        }
    }

    React.useEffect(() => {
        fetchData()
    }, [])

    const handleDelete = async (docId: string) => {
        if (!confirm('Yakin ingin menghapus dokumen ini?')) return

        setDeleteStatus({ id: docId, status: 'loading' })
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/documents/${docId}`, {
                method: 'DELETE'
            })
            if (!res.ok) throw new Error('Delete failed')

            setDeleteStatus({ id: docId, status: 'success' })
            setTimeout(() => {
                setDeleteStatus(null)
                fetchData() // Refresh list
            }, 1000)
        } catch {
            setDeleteStatus({ id: docId, status: 'error' })
            setTimeout(() => setDeleteStatus(null), 2000)
        }
    }

    const formatBytes = (bytes: number) => {
        if (bytes === 0) return '0 B'
        const k = 1024
        const sizes = ['B', 'KB', 'MB', 'GB']
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr)
        const now = new Date()
        const diff = now.getTime() - date.getTime()
        const minutes = Math.floor(diff / 60000)
        const hours = Math.floor(diff / 3600000)
        const days = Math.floor(diff / 86400000)

        if (minutes < 1) return 'Baru saja'
        if (minutes < 60) return `${minutes} menit yang lalu`
        if (hours < 24) return `${hours} jam yang lalu`
        return `${days} hari yang lalu`
    }

    return (
        <div className="p-6 lg:p-8 pb-32 space-y-8">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">
                        Control Center
                    </h1>
                    <p className="text-slate-400 mt-1">Kelola knowledge base dan monitor performa</p>
                </div>
                <div className="flex gap-3">
                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${backendOnline
                        ? 'bg-green-500/10 border border-green-500/20 text-green-400'
                        : 'bg-red-500/10 border border-red-500/20 text-red-400'
                        }`}>
                        <div className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                        {backendOnline ? 'System Online' : 'Backend Offline'}
                    </div>
                </div>
            </div>

            {/* Error Banner */}
            {error && (
                <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                    <AlertCircle className="w-5 h-5 text-red-400" />
                    <p className="text-red-400">{error}</p>
                    <button
                        onClick={fetchData}
                        className="ml-auto px-4 py-2 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-red-400 text-sm transition-colors"
                    >
                        Coba Lagi
                    </button>
                </div>
            )}

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatsCard
                    title="Total Dokumen"
                    value={stats?.total_documents || 0}
                    change={documents.length > 0 ? `${documents.length} aktif` : 'Belum ada'}
                    icon={FileText}
                    color="blue"
                />
                <StatsCard
                    title="Total Queries"
                    value={stats?.total_queries || 0}
                    change={stats?.last_query_at ? formatDate(stats.last_query_at) : 'Belum ada'}
                    icon={Activity}
                    color="purple"
                    trend="up"
                />
                <StatsCard
                    title="Ukuran Dokumen"
                    value={formatBytes(stats?.total_size_bytes || 0)}
                    change="Total upload"
                    icon={Clock}
                    color="cyan"
                />
                <StatsCard
                    title="Vector DB Size"
                    value={formatBytes(stats?.vector_db_size_bytes || 0)}
                    change="FAISS index"
                    icon={Database}
                    color="green"
                />
            </div>

            {/* Analytics Section */}
            <div className="space-y-6">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <Activity className="w-5 h-5 text-purple-400" />
                    Analytics Dashboard
                </h2>
                <AnalyticsChart />
            </div>

            {/* Feedback Analytics Section */}
            <div className="space-y-6">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <ThumbsUp className="w-5 h-5 text-emerald-400" />
                    User Feedback
                </h2>
                <FeedbackDashboard />
            </div>

            {/* QA Testing Section */}
            <div className="space-y-6">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
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
