"use client"

/**
 * ChatBubble Component - AKASIA
 * Komponen gelembung chat dengan:
 * - Confidence Badge
 * - Feedback Buttons (👍/👎)
 * - Related Questions
 */

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { User, Sparkles, BookOpen, Shield, ShieldCheck, ShieldAlert, ThumbsUp, ThumbsDown, MessageCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

interface ChatBubbleProps {
    role: "user" | "ai"
    content: string
    citations?: string[]
    isTyping?: boolean
    confidence?: number
    relatedQuestions?: string[]
    feedback?: "up" | "down" | null
    messageIndex?: number
    onFeedback?: (rating: "up" | "down") => void
    onQuestionClick?: (question: string) => void
}

// Animation variants untuk performa optimal
const bubbleVariants = {
    hidden: {
        opacity: 0,
        y: 20,
        scale: 0.95
    },
    visible: {
        opacity: 1,
        y: 0,
        scale: 1,
        transition: {
            type: "spring" as const,
            stiffness: 400,
            damping: 30,
            mass: 0.8
        }
    }
}

const avatarVariants = {
    hidden: { scale: 0, opacity: 0 },
    visible: {
        scale: 1,
        opacity: 1,
        transition: {
            type: "spring" as const,
            stiffness: 500,
            damping: 25,
            delay: 0.1
        }
    }
}

const citationVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: (i: number) => ({
        opacity: 1,
        y: 0,
        transition: {
            delay: 0.3 + (i * 0.1),
            duration: 0.3,
            ease: [0.4, 0, 0.2, 1] as const
        }
    })
}

// Komponen Typing Indicator dengan animasi halus
function TypingIndicator() {
    return (
        <div className="flex gap-1.5 items-center h-6 px-1">
            {[0, 1, 2].map((i) => (
                <motion.div
                    key={i}
                    className="w-2 h-2 rounded-full bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400"
                    animate={{
                        y: [0, -8, 0],
                        opacity: [0.5, 1, 0.5],
                    }}
                    transition={{
                        duration: 0.8,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                />
            ))}
        </div>
    )
}

// Confidence Badge Component
function ConfidenceBadge({ confidence }: { confidence: number }) {
    const getConfidenceStyle = () => {
        if (confidence >= 80) return {
            bg: "bg-emerald-500/20",
            border: "border-emerald-500/30",
            text: "text-emerald-400",
            icon: ShieldCheck,
            label: "Tinggi"
        }
        if (confidence >= 50) return {
            bg: "bg-amber-500/20",
            border: "border-amber-500/30",
            text: "text-amber-400",
            icon: Shield,
            label: "Sedang"
        }
        return {
            bg: "bg-red-500/20",
            border: "border-red-500/30",
            text: "text-red-400",
            icon: ShieldAlert,
            label: "Rendah"
        }
    }

    const style = getConfidenceStyle()
    const Icon = style.icon

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className={cn(
                "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs",
                "border backdrop-blur-sm",
                style.bg, style.border, style.text
            )}
        >
            <Icon className="w-3.5 h-3.5" />
            <span>{confidence}%</span>
            <span className="hidden sm:inline">• {style.label}</span>
        </motion.div>
    )
}

export function ChatBubble({
    role,
    content,
    citations,
    isTyping,
    confidence,
    relatedQuestions,
    feedback,
    onFeedback,
    onQuestionClick
}: ChatBubbleProps) {
    const isAI = role === "ai"

    return (
        <motion.div
            variants={bubbleVariants}
            initial="hidden"
            animate="visible"
            className={cn(
                "flex w-full mb-6",
                isAI ? "justify-start" : "justify-end"
            )}
        >
            <div className={cn(
                "flex max-w-[85%] md:max-w-[75%] gap-3",
                isAI ? "flex-row" : "flex-row-reverse"
            )}>
                {/* Avatar dengan animasi pop-in */}
                <motion.div
                    variants={avatarVariants}
                    initial="hidden"
                    animate="visible"
                    className={cn(
                        "w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-lg",
                        "transform-gpu", // GPU acceleration hint
                        isAI
                            ? "bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500"
                            : "bg-gradient-to-br from-slate-700 to-slate-800 border border-slate-600"
                    )}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                >
                    {isAI ? (
                        <Sparkles className="w-5 h-5 text-white" />
                    ) : (
                        <User className="w-5 h-5 text-slate-300" />
                    )}
                </motion.div>

                {/* Message Content */}
                <div className="flex flex-col gap-2">
                    <motion.div
                        className={cn(
                            "px-5 py-4 rounded-2xl backdrop-blur-sm",
                            "shadow-lg transform-gpu",
                            "border text-sm md:text-base leading-relaxed",
                            isAI
                                ? "bg-slate-900/60 border-slate-700/50 text-slate-100 rounded-tl-sm"
                                : "bg-gradient-to-br from-blue-600/80 to-purple-600/80 border-white/10 text-white rounded-tr-sm"
                        )}
                        whileHover={{
                            scale: 1.01,
                            transition: { duration: 0.2 }
                        }}
                    >
                        <AnimatePresence mode="wait">
                            {isTyping ? (
                                <motion.div
                                    key="typing"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                >
                                    <TypingIndicator />
                                </motion.div>
                            ) : (
                                <motion.div
                                    key="content"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="prose prose-invert prose-sm max-w-none"
                                >
                                    {isAI ? (
                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm]}
                                            components={{
                                                h1: ({ children }) => <h3 className="text-lg font-bold text-white mt-3 mb-2">{children}</h3>,
                                                h2: ({ children }) => <h4 className="text-base font-semibold text-white mt-2 mb-1">{children}</h4>,
                                                h3: ({ children }) => <h5 className="text-sm font-semibold text-slate-200 mt-2 mb-1">{children}</h5>,
                                                p: ({ children }) => <p className="text-slate-100 mb-2 leading-relaxed">{children}</p>,
                                                ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-1 text-slate-200">{children}</ul>,
                                                ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-1 text-slate-200">{children}</ol>,
                                                li: ({ children }) => <li className="text-slate-200">{children}</li>,
                                                strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
                                                em: ({ children }) => <em className="italic text-blue-300">{children}</em>,
                                                code: ({ children }) => <code className="px-1.5 py-0.5 bg-slate-700/50 rounded text-blue-300 text-xs">{children}</code>,
                                                blockquote: ({ children }) => <blockquote className="border-l-2 border-blue-400 pl-3 italic text-slate-300">{children}</blockquote>,
                                            }}
                                        >
                                            {content}
                                        </ReactMarkdown>
                                    ) : (
                                        <p className="whitespace-pre-wrap">{content}</p>
                                    )}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>

                    {/* Confidence Badge () */}
                    {isAI && confidence !== undefined && !isTyping && (
                        <div className="flex items-center gap-2 ml-1">
                            <ConfidenceBadge confidence={confidence} />
                        </div>
                    )}

                    {/* Citations dengan stagger animation */}
                    {isAI && citations && citations.length > 0 && !isTyping && (
                        <motion.div
                            initial="hidden"
                            animate="visible"
                            className="flex flex-wrap gap-2 mt-1 ml-1"
                        >
                            {citations.map((cite, i) => (
                                <motion.div
                                    key={i}
                                    custom={i}
                                    variants={citationVariants}
                                    className={cn(
                                        "flex items-center gap-1.5 px-3 py-1.5 rounded-full",
                                        "bg-blue-500/10 border border-blue-500/20",
                                        "text-blue-300 text-xs",
                                        "hover:bg-blue-500/20 hover:border-blue-400/30",
                                        "transition-colors duration-200 cursor-pointer",
                                        "transform-gpu"
                                    )}
                                    whileHover={{ scale: 1.02, y: -1 }}
                                    whileTap={{ scale: 0.98 }}
                                >
                                    <BookOpen className="w-3 h-3" />
                                    <span className="truncate max-w-[150px]">{cite}</span>
                                </motion.div>
                            ))}
                        </motion.div>
                    )}

                    {/*: Feedback Buttons */}
                    {isAI && content && !isTyping && onFeedback && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.5 }}
                            className="flex items-center gap-2 mt-2 ml-1"
                        >
                            <span className="text-xs text-slate-500 mr-1">Apakah jawaban ini membantu?</span>
                            <button
                                onClick={() => onFeedback("up")}
                                className={cn(
                                    "p-1.5 rounded-lg transition-all duration-200",
                                    feedback === "up"
                                        ? "bg-emerald-500/20 text-emerald-400"
                                        : "hover:bg-slate-700 text-slate-400 hover:text-emerald-400"
                                )}
                            >
                                <ThumbsUp className="w-4 h-4" />
                            </button>
                            <button
                                onClick={() => onFeedback("down")}
                                className={cn(
                                    "p-1.5 rounded-lg transition-all duration-200",
                                    feedback === "down"
                                        ? "bg-red-500/20 text-red-400"
                                        : "hover:bg-slate-700 text-slate-400 hover:text-red-400"
                                )}
                            >
                                <ThumbsDown className="w-4 h-4" />
                            </button>
                        </motion.div>
                    )}

                    {/*: Related Questions */}
                    {isAI && relatedQuestions && relatedQuestions.length > 0 && !isTyping && onQuestionClick && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.6 }}
                            className="mt-3 ml-1"
                        >
                            <div className="flex items-center gap-1.5 mb-2 text-xs text-slate-500">
                                <MessageCircle className="w-3.5 h-3.5" />
                                <span>Pertanyaan terkait:</span>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {relatedQuestions.map((q, i) => (
                                    <motion.button
                                        key={i}
                                        onClick={() => onQuestionClick(q)}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        className={cn(
                                            "px-3 py-1.5 rounded-full text-xs",
                                            "bg-purple-500/10 border border-purple-500/20",
                                            "text-purple-300 hover:bg-purple-500/20",
                                            "transition-colors duration-200"
                                        )}
                                    >
                                        {q}
                                    </motion.button>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </div>
            </div>
        </motion.div>
    )
}
