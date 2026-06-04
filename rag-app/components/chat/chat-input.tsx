"use client"

/**
 * ChatInput Component - AKASIA
 * Input chat dengan animasi glow dan micro-interactions
 */

import * as React from "react"
import { motion } from "framer-motion"
import { SendHorizontal, Loader2, Sparkles } from "lucide-react"
import { useChat } from "@/components/chat-provider"

export function ChatInput({ onSend }: { onSend: (message: string) => void }) {
    const [value, setValue] = React.useState("")
    const [isFocused, setIsFocused] = React.useState(false)
    const { isTyping } = useChat()
    const inputRef = React.useRef<HTMLInputElement>(null)

    const handleSend = () => {
        if (value.trim() && !isTyping) {
            onSend(value)
            setValue("")
        }
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <div className="fixed bottom-6 left-0 right-0 flex justify-center px-4 z-40 md:pl-64">
            <motion.div
                className="relative w-full max-w-3xl"
                initial={{ y: 100, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{
                    type: "spring",
                    stiffness: 300,
                    damping: 30,
                    delay: 0.2
                }}
            >
                {/* Animated Glow Background */}
                <motion.div
                    className="absolute -inset-1 bg-gradient-to-r from-blue-500 via-purple-500 to-cyan-500 rounded-2xl blur-lg"
                    animate={{
                        opacity: isFocused ? 0.4 : 0.15,
                        scale: isFocused ? 1.02 : 1,
                    }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                />

                {/* Glass Container */}
                <motion.div
                    className="relative flex items-center gap-2 p-2 rounded-2xl bg-slate-950/90 backdrop-blur-xl border border-white/10 shadow-2xl"
                    animate={{
                        borderColor: isFocused
                            ? "rgba(139, 92, 246, 0.3)"
                            : "rgba(255, 255, 255, 0.1)"
                    }}
                    transition={{ duration: 0.2 }}
                >
                    {/* AI Icon */}
                    <motion.div
                        className="pl-3 text-purple-400"
                        animate={{
                            rotate: isFocused ? [0, 10, -10, 0] : 0,
                            scale: isFocused ? 1.1 : 1
                        }}
                        transition={{ duration: 0.5 }}
                    >
                        <Sparkles className="w-5 h-5" />
                    </motion.div>

                    <input
                        ref={inputRef}
                        type="text"
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        onFocus={() => setIsFocused(true)}
                        onBlur={() => setIsFocused(false)}
                        placeholder="Tanyakan seputar akademik ILKOM..."
                        disabled={isTyping}
                        className="flex-1 bg-transparent border-none outline-none text-white placeholder-slate-500 px-3 py-3 disabled:opacity-50 text-sm md:text-base"
                    />

                    {/* Send Button */}
                    <motion.button
                        onClick={handleSend}
                        disabled={isTyping || !value.trim()}
                        className="p-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl shadow-lg disabled:opacity-40 disabled:cursor-not-allowed"
                        whileHover={{ scale: 1.05, boxShadow: "0 0 20px rgba(139, 92, 246, 0.4)" }}
                        whileTap={{ scale: 0.95 }}
                        transition={{ type: "spring", stiffness: 400, damping: 25 }}
                    >
                        {isTyping ? (
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                            >
                                <Loader2 className="w-5 h-5" />
                            </motion.div>
                        ) : (
                            <SendHorizontal className="w-5 h-5" />
                        )}
                    </motion.button>
                </motion.div>

                {/* Hint Text */}
                <motion.p
                    className="text-center text-xs text-slate-500 mt-2"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0.6 }}
                    transition={{ delay: 0.5 }}
                >
                    AKASIA • Powered by Kelompok 5
                </motion.p>
            </motion.div>
        </div>
    )
}
