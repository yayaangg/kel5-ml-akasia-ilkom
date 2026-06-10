"use client"

/**
 * Landing Page - AKASIA v2.4
 * AI-Themed Modern Landing with Neural Network Animations
 * Scope: FMIPA UHO
 */

import * as React from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import {
    GraduationCap, BarChart3, Sparkles, ArrowRight, BookOpen, Clock, Shield, Zap,
    ChevronRight, Brain, Cpu, Network, BrainCircuit, Bot, Wand2, CircuitBoard
} from "lucide-react"

// Neural Network Animation Background
function NeuralBackground() {
    const nodes = React.useMemo(() =>
        Array.from({ length: 20 }, (_, i) => ({
            id: i,
            x: Math.random() * 100,
            y: Math.random() * 100,
            size: Math.random() * 4 + 2,
            delay: Math.random() * 2
        })), [])

    return (
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <svg className="w-full h-full opacity-20">
                <defs>
                    <linearGradient id="nodeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#3b82f6" />
                        <stop offset="100%" stopColor="#8b5cf6" />
                    </linearGradient>
                    <filter id="glow">
                        <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>

                {/* Connecting lines */}
                {nodes.slice(0, 10).map((node, i) => (
                    <motion.line
                        key={`line-${i}`}
                        x1={`${node.x}%`}
                        y1={`${node.y}%`}
                        x2={`${nodes[(i + 3) % nodes.length].x}%`}
                        y2={`${nodes[(i + 3) % nodes.length].y}%`}
                        stroke="url(#nodeGradient)"
                        strokeWidth="0.5"
                        initial={{ pathLength: 0, opacity: 0 }}
                        animate={{ pathLength: 1, opacity: [0.2, 0.5, 0.2] }}
                        transition={{
                            duration: 3,
                            delay: node.delay,
                            repeat: Infinity,
                            ease: "easeInOut"
                        }}
                    />
                ))}

                {/* Neural nodes */}
                {nodes.map((node) => (
                    <motion.circle
                        key={node.id}
                        cx={`${node.x}%`}
                        cy={`${node.y}%`}
                        r={node.size}
                        fill="url(#nodeGradient)"
                        filter="url(#glow)"
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{
                            scale: [1, 1.3, 1],
                            opacity: [0.5, 1, 0.5]
                        }}
                        transition={{
                            duration: 2 + Math.random(),
                            delay: node.delay,
                            repeat: Infinity,
                            ease: "easeInOut"
                        }}
                    />
                ))}
            </svg>
        </div>
    )
}

// Floating AI Icons
function FloatingIcons() {
    const icons = [Brain, Cpu, BrainCircuit, Bot, Wand2, CircuitBoard]

    return (
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
            {icons.map((Icon, i) => (
                <motion.div
                    key={i}
                    className="absolute text-purple-500/20"
                    style={{
                        left: `${10 + i * 15}%`,
                        top: `${20 + (i % 3) * 25}%`
                    }}
                    animate={{
                        y: [0, -20, 0],
                        rotate: [0, 10, -10, 0],
                        opacity: [0.2, 0.4, 0.2]
                    }}
                    transition={{
                        duration: 5 + i,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: i * 0.5
                    }}
                >
                    <Icon className="w-12 h-12" />
                </motion.div>
            ))}
        </div>
    )
}

// Typing Animation
function TypeWriter({ text, className }: { text: string; className?: string }) {
    const [displayed, setDisplayed] = React.useState("")

    React.useEffect(() => {
        let i = 0
        const timer = setInterval(() => {
            if (i <= text.length) {
                setDisplayed(text.slice(0, i))
                i++
            } else {
                clearInterval(timer)
            }
        }, 50)
        return () => clearInterval(timer)
    }, [text])

    return (
        <span className={className}>
            {displayed}
            <motion.span
                animate={{ opacity: [1, 0] }}
                transition={{ duration: 0.5, repeat: Infinity }}
                className="ml-1"
            >
                |
            </motion.span>
        </span>
    )
}

// Animation variants
const fadeUp = {
    hidden: { opacity: 0, y: 30 },
    visible: (i: number) => ({
        opacity: 1,
        y: 0,
        transition: { delay: i * 0.1, duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }
    })
}

const features = [
    {
        icon: Brain,
        title: "AI Conversation",
        description: "Didukung LLM canggih untuk percakapan natural seperti ChatGPT",
        color: "from-blue-500 to-cyan-500"
    },
    {
        icon: Network,
        title: "RAG Technology",
        description: "Retrieval Augmented Generation untuk jawaban berbasis dokumen asli",
        color: "from-purple-500 to-pink-500"
    },
    {
        icon: Zap,
        title: "Hybrid Search",
        description: "Kombinasi semantic search + BM25 untuk hasil paling relevan",
        color: "from-amber-500 to-orange-500"
    },
    {
        icon: Shield,
        title: "Neural Re-ranking",
        description: "Cross-encoder model untuk menyaring jawaban paling akurat",
        color: "from-green-500 to-emerald-500"
    }
]

const stats = [
    { value: "LLM", label: "AI Powered", icon: Brain },
    { value: "276", label: "Knowledge Chunks", icon: BookOpen },
    { value: "24/7", label: "Always Online", icon: Clock },
    { value: "<3s", label: "Response Time", icon: Zap }
]

export default function LandingPage() {
    return (
        <div className="min-h-screen overflow-hidden bg-[#0a0a12]">
            {/* Hero Section */}
            <section className="relative min-h-screen flex items-center justify-center px-6">
                {/* Neural Network Background */}
                <NeuralBackground />

                {/* Floating AI Icons */}
                <FloatingIcons />

                {/* Animated Background Orbs */}
                <div className="absolute inset-0 overflow-hidden pointer-events-none">
                    <motion.div
                        className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[100px]"
                        animate={{
                            x: [0, 80, 0],
                            y: [0, 50, 0],
                            scale: [1, 1.2, 1]
                        }}
                        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
                    />
                    <motion.div
                        className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-purple-500/15 rounded-full blur-[80px]"
                        animate={{
                            x: [0, -60, 0],
                            y: [0, -30, 0],
                            scale: [1, 1.3, 1]
                        }}
                        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
                    />
                    <motion.div
                        className="absolute top-1/2 left-1/2 w-[300px] h-[300px] bg-cyan-500/10 rounded-full blur-[60px]"
                        animate={{
                            x: [0, 40, -40, 0],
                            y: [0, -40, 40, 0]
                        }}
                        transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
                    />
                </div>

                <div className="relative z-10 max-w-5xl mx-auto text-center">
                    {/* AI Badge */}
                    <motion.div
                        custom={0}
                        variants={fadeUp}
                        initial="hidden"
                        animate="visible"
                        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/30 text-purple-300 text-sm mb-8 backdrop-blur-sm"
                    >
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                        >
                            <BrainCircuit className="w-5 h-5" />
                        </motion.div>
                        <span className="font-medium">Powered by Advanced AI & RAG Technology</span>
                        <motion.div
                            className="w-2 h-2 rounded-full bg-green-400"
                            animate={{ scale: [1, 1.3, 1], opacity: [1, 0.5, 1] }}
                            transition={{ duration: 1.5, repeat: Infinity }}
                        />
                    </motion.div>

                    {/* Main Title with Glow Effect */}
                    <motion.div
                        custom={1}
                        variants={fadeUp}
                        initial="hidden"
                        animate="visible"
                        className="relative"
                    >
                        <h1 className="text-6xl md:text-8xl font-black mb-2 relative">
                            <span className="absolute inset-0 text-blue-500/20 blur-2xl">AKASIA</span>
                            <span className="relative gradient-text">AKASIA</span>
                        </h1>
                        <motion.div
                            className="absolute -inset-4 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-cyan-500/10 rounded-3xl blur-xl -z-10"
                            animate={{ opacity: [0.5, 1, 0.5] }}
                            transition={{ duration: 3, repeat: Infinity }}
                        />
                    </motion.div>

                    <motion.p
                        custom={2}
                        variants={fadeUp}
                        initial="hidden"
                        animate="visible"
                        className="text-xl md:text-2xl text-slate-300 mb-2"
                    >
                        <TypeWriter text="Asisten Akademik Sistem Informasi Answering" />
                    </motion.p>

                    <motion.p
                        custom={3}
                        variants={fadeUp}
                        initial="hidden"
                        animate="visible"
                        className="text-lg text-slate-400 max-w-2xl mx-auto mb-12 flex items-center justify-center gap-2"
                    >
                        <Bot className="w-5 h-5 text-purple-400" />
                        AI Chatbot yang menjawab pertanyaan akademik FMIPA UHO dengan akurat
                    </motion.p>

                    {/* CTA Buttons */}
                    <motion.div
                        custom={4}
                        variants={fadeUp}
                        initial="hidden"
                        animate="visible"
                        className="flex flex-col sm:flex-row gap-4 justify-center"
                    >
                        <Link href="/chat">
                            <motion.button
                                className="group relative px-8 py-4 bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 bg-[length:200%_100%] rounded-2xl text-white font-semibold shadow-2xl shadow-purple-500/30 flex items-center gap-3 justify-center overflow-hidden"
                                whileHover={{ scale: 1.03, boxShadow: "0 25px 50px rgba(139, 92, 246, 0.4)" }}
                                whileTap={{ scale: 0.97 }}
                                animate={{ backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"] }}
                                transition={{ duration: 3, repeat: Infinity }}
                            >
                                <Sparkles className="w-5 h-5" />
                                Mulai Chat dengan AI
                                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />

                                {/* Shine effect */}
                                <motion.div
                                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12"
                                    animate={{ x: ["-200%", "200%"] }}
                                    transition={{ duration: 3, repeat: Infinity, repeatDelay: 2 }}
                                />
                            </motion.button>
                        </Link>
                        <Link href="/auth/login">
                            <motion.button
                                className="px-8 py-4 bg-white/5 border border-white/10 rounded-2xl text-white font-semibold flex items-center gap-3 justify-center hover:bg-white/10 hover:border-white/20 transition-all backdrop-blur-sm"
                                whileHover={{ scale: 1.03 }}
                                whileTap={{ scale: 0.97 }}
                            >
                                <BarChart3 className="w-5 h-5" />
                                Login Admin
                            </motion.button>
                        </Link>
                    </motion.div>

                    {/* Stats with Icons */}
                    <motion.div
                        custom={5}
                        variants={fadeUp}
                        initial="hidden"
                        animate="visible"
                        className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-20 max-w-4xl mx-auto"
                    >
                        {stats.map((stat, i) => (
                            <motion.div
                                key={i}
                                className="text-center p-4 rounded-2xl bg-white/[0.02] border border-white/[0.05] backdrop-blur-sm"
                                whileHover={{ scale: 1.05, borderColor: "rgba(139, 92, 246, 0.3)" }}
                            >
                                <stat.icon className="w-6 h-6 mx-auto mb-2 text-purple-400" />
                                <div className="text-3xl md:text-4xl font-bold gradient-text">{stat.value}</div>
                                <div className="text-sm text-slate-400 mt-1">{stat.label}</div>
                            </motion.div>
                        ))}
                    </motion.div>
                </div>

                {/* Scroll Indicator */}
                <motion.div
                    className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
                    animate={{ y: [0, 10, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                >
                    <span className="text-xs text-slate-500">Scroll</span>
                    <ChevronRight className="w-5 h-5 rotate-90 text-slate-500" />
                </motion.div>
            </section>

            {/* AI Features Section */}
            <section className="py-32 px-6 relative overflow-hidden">
                {/* Background Pattern */}
                <div className="absolute inset-0 opacity-5">
                    <div className="absolute inset-0" style={{
                        backgroundImage: `radial-gradient(circle at 1px 1px, rgb(139 92 246) 1px, transparent 0)`,
                        backgroundSize: '40px 40px'
                    }} />
                </div>

                <div className="max-w-6xl mx-auto relative">
                    <motion.div
                        className="text-center mb-20"
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                    >
                        <motion.div
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-sm mb-6"
                            whileHover={{ scale: 1.05 }}
                        >
                            <Cpu className="w-4 h-4" />
                            AI-Powered Features
                        </motion.div>
                        <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
                            Teknologi <span className="gradient-text">AI Canggih</span>
                        </h2>
                        <p className="text-slate-400 max-w-2xl mx-auto text-lg">
                            AKASIA menggunakan teknologi AI terdepan untuk memberikan jawaban yang akurat dan cepat
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {features.map((feature, i) => (
                            <motion.div
                                key={i}
                                className="relative p-6 rounded-3xl bg-gradient-to-b from-slate-900/80 to-slate-900/40 border border-slate-800/50 backdrop-blur-sm group overflow-hidden"
                                initial={{ opacity: 0, y: 30 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.1 }}
                                whileHover={{ y: -8, borderColor: "rgba(139, 92, 246, 0.4)" }}
                            >
                                {/* Glow on hover */}
                                <motion.div
                                    className="absolute inset-0 bg-gradient-to-br from-purple-500/0 to-blue-500/0 group-hover:from-purple-500/10 group-hover:to-blue-500/10 transition-all duration-500"
                                />

                                <div className={`relative w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-5 group-hover:scale-110 group-hover:rotate-3 transition-all duration-300 shadow-lg`}>
                                    <feature.icon className="w-7 h-7 text-white" />
                                </div>
                                <h3 className="relative text-xl font-semibold text-white mb-3">{feature.title}</h3>
                                <p className="relative text-slate-400">{feature.description}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Demo Preview Section */}
            <section className="py-32 px-6 relative">
                <div className="max-w-5xl mx-auto">
                    <motion.div
                        className="rounded-[2rem] bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 border border-slate-700/50 p-10 md:p-14 overflow-hidden relative"
                        initial={{ opacity: 0, scale: 0.95 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                    >
                        {/* Multiple Glow Effects */}
                        <div className="absolute top-0 right-0 w-80 h-80 bg-purple-500/20 rounded-full blur-[100px]" />
                        <div className="absolute bottom-0 left-0 w-60 h-60 bg-blue-500/20 rounded-full blur-[80px]" />

                        <div className="relative z-10 flex flex-col md:flex-row items-center gap-10">
                            <div className="flex-1">
                                <motion.div
                                    className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-sm mb-6"
                                    animate={{ boxShadow: ["0 0 0 0 rgba(34, 197, 94, 0.4)", "0 0 0 10px rgba(34, 197, 94, 0)", "0 0 0 0 rgba(34, 197, 94, 0)"] }}
                                    transition={{ duration: 2, repeat: Infinity }}
                                >
                                    <motion.div
                                        className="w-2 h-2 rounded-full bg-green-500"
                                        animate={{ scale: [1, 1.3, 1] }}
                                        transition={{ duration: 1, repeat: Infinity }}
                                    />
                                    AI System Online
                                </motion.div>
                                <h3 className="text-3xl md:text-4xl font-bold text-white mb-5">
                                    Coba Tanya <span className="gradient-text">AKASIA AI</span>
                                </h3>
                                <p className="text-slate-400 mb-8 text-lg">
                                    Tanyakan tentang masa studi, syarat kelulusan, prosedur cuti akademik,
                                    atau jadwal kalender akademik FMIPA UHO.
                                </p>
                                <Link href="/chat">
                                    <motion.button
                                        className="group px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl text-white font-semibold flex items-center gap-3 shadow-xl shadow-purple-500/20"
                                        whileHover={{ scale: 1.03, boxShadow: "0 20px 40px rgba(139, 92, 246, 0.3)" }}
                                        whileTap={{ scale: 0.97 }}
                                    >
                                        <Bot className="w-5 h-5" />
                                        Chat Sekarang
                                        <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                    </motion.button>
                                </Link>
                            </div>

                            {/* Chat Preview */}
                            <div className="flex-1 w-full">
                                <motion.div
                                    className="bg-slate-950/90 rounded-3xl border border-slate-700/50 p-5 space-y-4 shadow-2xl"
                                    initial={{ x: 50, opacity: 0 }}
                                    whileInView={{ x: 0, opacity: 1 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: 0.2 }}
                                >
                                    {/* User Message */}
                                    <motion.div
                                        className="flex gap-3"
                                        initial={{ x: 20, opacity: 0 }}
                                        whileInView={{ x: 0, opacity: 1 }}
                                        viewport={{ once: true }}
                                        transition={{ delay: 0.4 }}
                                    >
                                        <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center shrink-0">
                                            <GraduationCap className="w-5 h-5 text-slate-400" />
                                        </div>
                                        <div className="bg-gradient-to-r from-blue-600/80 to-purple-600/80 rounded-2xl rounded-tl-none px-5 py-4 text-sm text-white">
                                            Berapa masa studi maksimal S1?
                                        </div>
                                    </motion.div>

                                    {/* AI Message */}
                                    <motion.div
                                        className="flex gap-3"
                                        initial={{ x: -20, opacity: 0 }}
                                        whileInView={{ x: 0, opacity: 1 }}
                                        viewport={{ once: true }}
                                        transition={{ delay: 0.6 }}
                                    >
                                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center shrink-0 shadow-lg shadow-purple-500/30">
                                            <Sparkles className="w-5 h-5 text-white" />
                                        </div>
                                        <div className="bg-slate-800/60 rounded-2xl rounded-tl-none px-5 py-4 text-sm text-slate-200 border border-slate-700/50">
                                            <p className="mb-2">Masa studi maksimal program sarjana (S1) adalah <strong className="text-white">7 tahun akademik</strong> dengan beban studi minimal 144 SKS.</p>
                                            <div className="flex items-center gap-2 text-xs">
                                                <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded-full">📄 Sumber: Peraturan Akademik FMIPA</span>
                                                <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded-full">✓ 75%</span>
                                            </div>
                                        </div>
                                    </motion.div>
                                </motion.div>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-16 px-6 border-t border-slate-800/50 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-t from-purple-500/5 to-transparent" />
                <div className="max-w-5xl mx-auto text-center relative">
                    <motion.div
                        className="flex items-center justify-center gap-3 mb-6"
                        whileHover={{ scale: 1.05 }}
                    >
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center shadow-lg shadow-purple-500/30">
                            <BrainCircuit className="w-6 h-6 text-white" />
                        </div>
                        <span className="text-2xl font-bold gradient-text">AKASIA</span>
                    </motion.div>
                    <p className="text-slate-400 mb-4">
                        Asisten Akademik Berbasis AI untuk FMIPA Universitas Halu Oleo
                    </p>
                    <p className="text-slate-600 text-sm">
                        © 2025 AKASIA v2.4 • Built with Next.js, FastAPI, LangChain & Groq AI
                    </p>
                </div>
            </footer>
        </div>
    )
}