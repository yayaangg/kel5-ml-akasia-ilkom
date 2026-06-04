"use client"

import * as React from "react"
import { GlassCard } from "@/components/ui/glass-card"
import { Trash2, AlertTriangle, ShieldAlert, Cpu, CheckCircle2, AlertCircle, RefreshCw } from "lucide-react"

export default function SettingsPage() {
    const [loading, setLoading] = React.useState(false)
    const [status, setStatus] = React.useState<{ type: 'success' | 'error', message: string } | null>(null)
    const [backendOnline, setBackendOnline] = React.useState(true)

    const checkBackend = async () => {
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/health`)
            setBackendOnline(res.ok)
        } catch {
            setBackendOnline(false)
        }
    }

    React.useEffect(() => {
        checkBackend()
    }, [])

    const handleClearKnowledgeBase = async () => {
        const doubleConfirm = confirm("PERINGATAN KERAS!\n\nTindakan ini akan MENGHAPUS SEMUA dokumen dan vektor indeks RAG.\nSemua data chat dan referensi akademik akan hilang dari memori AI.\n\nApakah Anda yakin ingin melanjutkan?")
        if (!doubleConfirm) return

        setLoading(true)
        setStatus(null)
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/clear-knowledge-base`, {
                method: "POST"
            })
            const data = await res.json()
            if (res.ok) {
                setStatus({ type: 'success', message: 'Basis pengetahuan berhasil direset sepenuhnya!' })
            } else {
                throw new Error(data.detail || 'Reset failed')
            }
        } catch (err: any) {
            setStatus({ type: 'error', message: `Gagal mereset: ${err.message || 'Koneksi bermasalah'}` })
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="p-6 lg:p-8 pb-32 space-y-8">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">
                        Pengaturan Sistem
                    </h1>
                    <p className="text-slate-400 mt-1">Konfigurasi basis pengetahuan dan performa model AI</p>
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

            {status && (
                <div className={`flex items-center gap-3 p-4 border rounded-xl ${status.type === 'success'
                    ? 'bg-green-500/10 border-green-500/20 text-green-400'
                    : 'bg-red-500/10 border border-red-500/20 text-red-400'
                    }`}>
                    {status.type === 'success' ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                    <p>{status.message}</p>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Left: Model and System Info */}
                <div className="space-y-6">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <Cpu className="w-5 h-5 text-purple-400" />
                        Spesifikasi & Model AI
                    </h2>
                    
                    <GlassCard className="space-y-6 p-6">
                        <div className="space-y-4">
                            <div>
                                <label className="text-xs text-slate-400 uppercase tracking-wider">Embedding Model (Semantic Search)</label>
                                <div className="text-white font-medium mt-1 font-mono text-sm bg-white/5 p-2.5 rounded-lg border border-white/5">
                                    paraphrase-multilingual-MiniLM-L12-v2
                                </div>
                            </div>

                            <div>
                                <label className="text-xs text-slate-400 uppercase tracking-wider">Re-ranker Model (Neural Scoring)</label>
                                <div className="text-white font-medium mt-1 font-mono text-sm bg-white/5 p-2.5 rounded-lg border border-white/5">
                                    cross-encoder/ms-marco-MiniLM-L-6-v2
                                </div>
                            </div>

                            <div>
                                <label className="text-xs text-slate-400 uppercase tracking-wider">LLM Engine (Generation)</label>
                                <div className="text-white font-medium mt-1 font-mono text-sm bg-white/5 p-2.5 rounded-lg border border-white/5">
                                    llama-3.1-8b-instant (via Groq Cloud API)
                                </div>
                            </div>
                        </div>
                    </GlassCard>
                </div>

                {/* Right: Danger Zone */}
                <div className="space-y-6">
                    <h2 className="text-xl font-bold text-red-400 flex items-center gap-2">
                        <ShieldAlert className="w-5 h-5" />
                        Danger Zone
                    </h2>

                    <GlassCard className="border-red-500/20 p-6 space-y-6">
                        <div className="flex gap-4 items-start">
                            <AlertTriangle className="w-10 h-10 text-red-400 flex-shrink-0" />
                            <div>
                                <h3 className="text-lg font-semibold text-white">Reset Basis Pengetahuan</h3>
                                <p className="text-sm text-slate-400 mt-1">
                                    Tindakan ini akan menghapus semua file PDF yang terindeks dan mereset basis data vektor FAISS ke kondisi kosong. Tindakan ini tidak dapat dibatalkan.
                                </p>
                            </div>
                        </div>

                        <div className="pt-4 border-t border-white/5">
                            <button
                                onClick={handleClearKnowledgeBase}
                                disabled={loading || !backendOnline}
                                className="w-full flex items-center justify-center gap-2 py-3 bg-red-500/10 hover:bg-red-500/20 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed border border-red-500/20 hover:border-red-500/30 rounded-xl text-red-400 font-semibold transition-all"
                            >
                                {loading ? (
                                    <RefreshCw className="w-5 h-5 animate-spin" />
                                ) : (
                                    <Trash2 className="w-5 h-5" />
                                )}
                                Hapus Semua Dokumen & Reset Indeks
                            </button>
                        </div>
                    </GlassCard>
                </div>
            </div>
        </div>
    )
}
