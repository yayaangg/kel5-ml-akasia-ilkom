"use client"

/**
 * QueryTester Component - AKASIA v2.4
 * Batch test pertanyaan untuk QA di Admin Panel
 */

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Play, CheckCircle, XCircle, Clock, Plus, Trash2, Loader2, Download } from "lucide-react"

interface TestResult {
    query: string
    response: string
    confidence: number
    responseTime: number
    status: "pending" | "running" | "success" | "error"
}

const defaultQueries = [
    "Berapa lama masa studi S1?",
    "Apa syarat kelulusan cum laude?",
    "Bagaimana prosedur cuti akademik?",
    "Berapa SKS yang harus ditempuh D3?"
]

export function QueryTester() {
    const [queries, setQueries] = React.useState<string[]>(defaultQueries)
    const [results, setResults] = React.useState<TestResult[]>([])
    const [isRunning, setIsRunning] = React.useState(false)
    const [newQuery, setNewQuery] = React.useState("")

    const addQuery = () => {
        if (newQuery.trim() && !queries.includes(newQuery.trim())) {
            setQueries([...queries, newQuery.trim()])
            setNewQuery("")
        }
    }

    const removeQuery = (index: number) => {
        setQueries(queries.filter((_, i) => i !== index))
    }

    const runTests = async () => {
        setIsRunning(true)
        const newResults: TestResult[] = queries.map(q => ({
            query: q,
            response: "",
            confidence: 0,
            responseTime: 0,
            status: "pending"
        }))
        setResults(newResults)

        for (let i = 0; i < queries.length; i++) {
            // Update to running
            setResults(prev => prev.map((r, idx) =>
                idx === i ? { ...r, status: "running" } : r
            ))

            const startTime = Date.now()
            try {
                const res = await fetch("http://localhost:8000/api/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: queries[i] })
                })

                if (!res.ok) throw new Error("Request failed")

                const reader = res.body?.getReader()
                const decoder = new TextDecoder()
                let fullResponse = ""
                let confidence = 0

                while (reader) {
                    const { done, value } = await reader.read()
                    if (done) break

                    const chunk = decoder.decode(value)
                    const lines = chunk.split("\n").filter(Boolean)

                    for (const line of lines) {
                        try {
                            const data = JSON.parse(line)
                            if (data.response) fullResponse += data.response
                            if (data.confidence) confidence = data.confidence
                        } catch { }
                    }
                }

                const responseTime = Date.now() - startTime

                setResults(prev => prev.map((r, idx) =>
                    idx === i ? {
                        ...r,
                        response: fullResponse.slice(0, 200) + (fullResponse.length > 200 ? "..." : ""),
                        confidence,
                        responseTime,
                        status: confidence >= 50 ? "success" : "error"
                    } : r
                ))

            } catch (error) {
                setResults(prev => prev.map((r, idx) =>
                    idx === i ? {
                        ...r,
                        response: "Error: Request failed",
                        confidence: 0,
                        responseTime: Date.now() - startTime,
                        status: "error"
                    } : r
                ))
            }
        }

        setIsRunning(false)
    }

    const exportResults = () => {
        const data = results.map(r => ({
            query: r.query,
            response: r.response,
            confidence: r.confidence,
            responseTime: r.responseTime,
            status: r.status
        }))
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" })
        const url = URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = `query-test-results-${new Date().toISOString().slice(0, 10)}.json`
        a.click()
    }

    const passCount = results.filter(r => r.status === "success").length
    const failCount = results.filter(r => r.status === "error").length

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white">Query Testing Tool</h3>
                <div className="flex gap-2">
                    {results.length > 0 && (
                        <button
                            onClick={exportResults}
                            className="flex items-center gap-2 px-3 py-2 bg-slate-700/50 hover:bg-slate-700 rounded-lg text-slate-300 text-sm transition-colors"
                        >
                            <Download className="w-4 h-4" />
                            Export
                        </button>
                    )}
                    <button
                        onClick={runTests}
                        disabled={isRunning || queries.length === 0}
                        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 rounded-lg text-white text-sm font-medium transition-all"
                    >
                        {isRunning ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                            <Play className="w-4 h-4" />
                        )}
                        {isRunning ? "Running..." : "Run Tests"}
                    </button>
                </div>
            </div>

            {/* Add Query Input */}
            <div className="flex gap-2">
                <input
                    type="text"
                    value={newQuery}
                    onChange={(e) => setNewQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && addQuery()}
                    placeholder="Tambah pertanyaan untuk ditest..."
                    className="flex-1 px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-purple-500"
                />
                <button
                    onClick={addQuery}
                    className="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-white transition-colors"
                >
                    <Plus className="w-5 h-5" />
                </button>
            </div>

            {/* Query List */}
            <div className="space-y-2">
                {queries.map((query, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex items-center gap-3 p-3 bg-slate-800/30 border border-slate-700/50 rounded-lg group"
                    >
                        <span className="text-slate-400 text-sm font-mono w-6">{i + 1}.</span>
                        <span className="flex-1 text-slate-200 text-sm">{query}</span>
                        <button
                            onClick={() => removeQuery(i)}
                            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded text-slate-500 hover:text-red-400 transition-all"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </motion.div>
                ))}
            </div>

            {/* Results Summary */}
            {results.length > 0 && (
                <div className="flex gap-4 p-4 bg-slate-800/30 border border-slate-700/50 rounded-lg">
                    <div className="flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                        <span className="text-emerald-400 font-medium">{passCount} Passed</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <XCircle className="w-5 h-5 text-red-400" />
                        <span className="text-red-400 font-medium">{failCount} Failed</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                        <Clock className="w-5 h-5" />
                        <span>Avg: {Math.round(results.reduce((a, b) => a + b.responseTime, 0) / results.length)}ms</span>
                    </div>
                </div>
            )}

            {/* Results Table */}
            <AnimatePresence>
                {results.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="bg-slate-900/50 border border-slate-700/50 rounded-xl overflow-hidden"
                    >
                        <table className="w-full text-left text-sm">
                            <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase">
                                <tr>
                                    <th className="p-3">Query</th>
                                    <th className="p-3">Response</th>
                                    <th className="p-3 text-center">Confidence</th>
                                    <th className="p-3 text-center">Time</th>
                                    <th className="p-3 text-center">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                                {results.map((result, i) => (
                                    <tr key={i} className="text-slate-300">
                                        <td className="p-3 max-w-[200px] truncate">{result.query}</td>
                                        <td className="p-3 max-w-[300px]">
                                            <p className="line-clamp-2 text-xs text-slate-400">
                                                {result.response || "..."}
                                            </p>
                                        </td>
                                        <td className="p-3 text-center">
                                            {result.status === "running" ? (
                                                <span className="text-slate-500">-</span>
                                            ) : (
                                                <span className={`font-medium ${result.confidence >= 80 ? "text-emerald-400" :
                                                        result.confidence >= 50 ? "text-amber-400" : "text-red-400"
                                                    }`}>
                                                    {result.confidence}%
                                                </span>
                                            )}
                                        </td>
                                        <td className="p-3 text-center text-slate-500">
                                            {result.responseTime > 0 ? `${result.responseTime}ms` : "-"}
                                        </td>
                                        <td className="p-3 text-center">
                                            {result.status === "pending" && (
                                                <span className="text-slate-500">Pending</span>
                                            )}
                                            {result.status === "running" && (
                                                <Loader2 className="w-4 h-4 animate-spin mx-auto text-blue-400" />
                                            )}
                                            {result.status === "success" && (
                                                <CheckCircle className="w-4 h-4 mx-auto text-emerald-400" />
                                            )}
                                            {result.status === "error" && (
                                                <XCircle className="w-4 h-4 mx-auto text-red-400" />
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
