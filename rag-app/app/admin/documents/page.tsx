"use client"

import * as React from "react"
import { UploadZone } from "@/components/admin/upload-zone"
import { GlassCard } from "@/components/ui/glass-card"
import {
    FileText,
    Trash2,
    RefreshCw,
    AlertCircle,
    CheckCircle
} from "lucide-react"

interface Document {
    id: string
    filename: string
    size_bytes: number
    uploaded_at: string
    status: string
    chunks_count: number
}

export default function DocumentsPage() {
    const [documents, setDocuments] = React.useState<Document[]>([])
    const [loading, setLoading] = React.useState(true)
    const [error, setError] = React.useState<string | null>(null)

    const [deleteStatus, setDeleteStatus] = React.useState<{
        id: string
        status: "loading" | "success" | "error"
    } | null>(null)

    const [backendOnline, setBackendOnline] = React.useState(true)

    const API =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

    // =========================
    // FETCH
    // =========================
    const fetchData = async () => {
        setLoading(true)
        setError(null)

        try {
            const token = localStorage.getItem("admin_token")

            const res = await fetch(`${API}/api/documents`, {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            })

            if (res.status === 401) {
                throw new Error("Unauthorized (token invalid / missing)")
            }

            if (!res.ok) {
                throw new Error("Gagal mengambil data")
            }

            const data = await res.json()

            setDocuments(data.documents || [])
            setBackendOnline(true)

        } catch (err: any) {
            setError(err.message)
            setBackendOnline(false)

        } finally {
            setLoading(false)
        }
    }

    React.useEffect(() => {
        fetchData()
    }, [])

    // =========================
    // DELETE
    // =========================
    const handleDelete = async (docId: string) => {
        if (!confirm("Yakin ingin menghapus dokumen ini?")) return

        setDeleteStatus({ id: docId, status: "loading" })

        try {
            const token = localStorage.getItem("admin_token")

            const res = await fetch(
                `${API}/api/documents/${docId}`,
                {
                    method: "DELETE",
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            )

            if (res.status === 401) {
                throw new Error("Unauthorized")
            }

            if (!res.ok) {
                throw new Error("Delete gagal")
            }

            setDeleteStatus({ id: docId, status: "success" })

            setTimeout(() => {
                setDeleteStatus(null)
                fetchData()
            }, 1000)

        } catch (err: any) {
            setDeleteStatus({ id: docId, status: "error" })

            setTimeout(() => setDeleteStatus(null), 2000)
        }
    }

    // =========================
    // FORMAT SIZE
    // =========================
    const formatBytes = (bytes: number) => {
        if (!bytes) return "0 B"

        const k = 1024
        const sizes = ["B", "KB", "MB", "GB"]
        const i = Math.floor(Math.log(bytes) / Math.log(k))

        return (
            parseFloat((bytes / Math.pow(k, i)).toFixed(2)) +
            " " +
            sizes[i]
        )
    }

    // =========================
    // UI
    // =========================
    return (
        <div className="p-6 lg:p-8 pb-32 space-y-8">

            {/* HEADER */}
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">
                        Manajemen Dokumen
                    </h1>
                    <p className="text-slate-400 mt-1">
                        Upload dan kelola dokumen basis pengetahuan AI
                    </p>
                </div>

                <div
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm ${
                        backendOnline
                            ? "bg-green-500/10 border border-green-500/20 text-green-400"
                            : "bg-red-500/10 border border-red-500/20 text-red-400"
                    }`}
                >
                    <div
                        className={`w-2 h-2 rounded-full ${
                            backendOnline
                                ? "bg-green-500 animate-pulse"
                                : "bg-red-500"
                        }`}
                    />
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
                        className="ml-auto px-4 py-2 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-red-400 text-sm"
                    >
                        Coba Lagi
                    </button>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* LEFT */}
                <div className="lg:col-span-2 space-y-4">

                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold text-white">
                            Daftar Dokumen
                        </h2>

                        <button
                            onClick={fetchData}
                            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-slate-400 hover:text-white text-sm"
                        >
                            <RefreshCw
                                className={`w-4 h-4 ${
                                    loading ? "animate-spin" : ""
                                }`}
                            />
                            Refresh
                        </button>
                    </div>

                    <GlassCard className="p-0 overflow-hidden">

                        {loading ? (
                            <div className="p-8 text-center text-slate-400">
                                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                                Memuat data...
                            </div>
                        ) : documents.length === 0 ? (
                            <div className="p-8 text-center text-slate-400">
                                <FileText className="w-10 h-10 mx-auto mb-3 opacity-50" />
                                Belum ada dokumen
                            </div>
                        ) : (
                            <table className="w-full text-left">

                                <thead className="bg-white/5 text-slate-400 text-xs uppercase">
                                    <tr>
                                        <th className="p-4">Nama</th>
                                        <th className="p-4">Ukuran</th>
                                        <th className="p-4">Status</th>
                                        <th className="p-4 text-right">
                                            Aksi
                                        </th>
                                    </tr>
                                </thead>

                                <tbody className="divide-y divide-white/5 text-sm">

                                    {documents.map((doc) => (
                                        <tr
                                            key={doc.id}
                                            className="hover:bg-white/5"
                                        >
                                            <td className="p-4 text-white flex items-center gap-2">
                                                <FileText className="w-4 h-4 text-blue-400" />
                                                {doc.filename}
                                            </td>

                                            <td className="p-4 text-slate-400">
                                                {formatBytes(doc.size_bytes)}
                                            </td>

                                            <td className="p-4">
                                                <span className="px-2 py-1 text-xs rounded-full bg-green-500/10 text-green-400">
                                                    {doc.status}
                                                </span>
                                            </td>

                                            <td className="p-4 text-right">
                                                {deleteStatus?.id === doc.id ? (
                                                    deleteStatus.status === "loading" ? (
                                                        <RefreshCw className="w-4 h-4 animate-spin" />
                                                    ) : deleteStatus.status === "success" ? (
                                                        <CheckCircle className="w-4 h-4 text-green-400" />
                                                    ) : (
                                                        <AlertCircle className="w-4 h-4 text-red-400" />
                                                    )
                                                ) : (
                                                    <button
                                                        onClick={() =>
                                                            handleDelete(doc.id)
                                                        }
                                                        className="text-red-400 hover:text-red-300"
                                                    >
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))}

                                </tbody>
                            </table>
                        )}
                    </GlassCard>
                </div>

                {/* RIGHT */}
                <div className="space-y-4">
                    <h2 className="text-xl font-bold text-white">
                        Upload Baru
                    </h2>

                    <UploadZone onUploadComplete={fetchData} />
                </div>

            </div>
        </div>
    )
}