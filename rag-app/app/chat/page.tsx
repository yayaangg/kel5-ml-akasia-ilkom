"use client"

/**
 * Home Page - AKASIA v2.0
 * Halaman utama chat dengan animasi modern
 */

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ChatInput } from "@/components/chat/chat-input"
import { ChatBubble } from "@/components/chat/chat-bubble"
import { MessageSquare, Sparkles, GraduationCap } from "lucide-react"
import { useChat } from "@/components/chat-provider"

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.2 }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: "spring" as const, stiffness: 300, damping: 25 }
  }
}

const questionVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: {
      delay: 0.4 + (i * 0.1),
      type: "spring" as const,
      stiffness: 300,
      damping: 25
    }
  }),
  hover: {
    scale: 1.02,
    y: -4,
    boxShadow: "0 10px 30px rgba(139, 92, 246, 0.15)",
    transition: { type: "spring" as const, stiffness: 400, damping: 20 }
  },
  tap: { scale: 0.98 }
}

export default function Home() {
  const { messages, isTyping, sendMessage, submitFeedback } = useChat()
  const messagesEndRef = React.useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  React.useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  const handleSend = (content: string) => {
    sendMessage(content)
  }

  const suggestedQuestions = [
    { text: "Berapa masa studi maksimal S1?", icon: "📚" },
    { text: "Bagaimana prosedur cuti akademik?", icon: "📋" },
    { text: "Apa syarat kelulusan cum laude?", icon: "🎓" },
    { text: "Berapa SKS yang harus ditempuh D3?", icon: "📊" }
  ]

  return (
    <div className="flex flex-col h-[100dvh] max-w-4xl mx-auto px-4 pt-20 md:pt-8 pb-28 md:pb-32">
      <div className="flex-1 overflow-y-auto scrollbar-hide py-4">
        <AnimatePresence mode="wait">
          {messages.length === 0 ? (
            /* Empty State - Welcome Screen */
            <motion.div
              key="welcome"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              exit={{ opacity: 0, scale: 0.95 }}
              className="flex flex-col items-center justify-center min-h-[70vh] md:h-full text-center space-y-6 sm:space-y-8 py-4 sm:py-12"
            >
              {/* Animated Logo */}
              <motion.div
                variants={itemVariants}
                className="relative"
              >
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full blur-2xl opacity-30"
                  animate={{
                    scale: [1, 1.2, 1],
                    opacity: [0.2, 0.4, 0.2]
                  }}
                  transition={{
                    duration: 3,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />
                <div className="relative p-4 sm:p-6 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/10 backdrop-blur-sm">
                  <GraduationCap className="w-10 h-10 sm:w-14 sm:h-14 text-blue-400" />
                </div>
              </motion.div>

              {/* Title & Description */}
              <motion.div variants={itemVariants} className="space-y-2 sm:space-y-4 px-4">
                <h1 className="text-3xl sm:text-5xl font-bold gradient-text">
                  AKASIA
                </h1>
                <p className="text-slate-400 text-sm sm:text-lg max-w-lg leading-relaxed">
                  Asisten Akademik AI untuk Universitas Halu Oleo
                </p>
                <p className="text-slate-500 text-xs sm:text-sm">
                  Tanyakan seputar peraturan akademik, kalender, dan informasi kampus
                </p>
              </motion.div>

              {/* Suggested Questions Grid */}
              <motion.div
                variants={itemVariants}
                className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 sm:gap-3 w-full max-w-2xl mt-4 sm:mt-6 px-2 sm:px-0"
              >
                {suggestedQuestions.map((question, i) => (
                  <motion.button
                    key={i}
                    custom={i}
                    variants={questionVariants}
                    initial="hidden"
                    animate="visible"
                    whileHover="hover"
                    whileTap="tap"
                    onClick={() => sendMessage(question.text)}
                    className="p-3.5 sm:p-4 text-left text-xs sm:text-sm bg-slate-900/50 hover:bg-slate-800/60 border border-slate-700/50 rounded-xl text-slate-300 hover:text-white backdrop-blur-sm group transform-gpu"
                  >
                    <span className="text-lg sm:text-xl mb-1 sm:mb-2 block">{question.icon}</span>
                    <span className="font-medium">{question.text}</span>
                    <motion.div
                      className="mt-1.5 hidden sm:flex items-center gap-1 text-[10px] sm:text-xs text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Sparkles className="w-3 h-3" />
                      <span>Klik untuk bertanya</span>
                    </motion.div>
                  </motion.button>
                ))}
              </motion.div>
            </motion.div>
          ) : (
            /* Chat Messages View */
            <motion.div
              key="chat"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-4"
            >
              {/* Header - Hidden on Mobile due to Mobile Header Bar */}
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center mb-6 mt-2 space-y-1 hidden md:block"
              >
                <h1 className="text-2xl font-bold gradient-text">
                  AKASIA
                </h1>
                <p className="text-slate-500 text-xs">
                  Asisten Akademik v2.2
                </p>
              </motion.div>

              {/* Messages */}
              {messages.map((msg, i) => (
                <ChatBubble
                  key={i}
                  role={msg.role}
                  content={msg.content}
                  citations={msg.citations}
                  confidence={msg.confidence}
                  relatedQuestions={msg.relatedQuestions}
                  feedback={msg.feedback}
                  messageIndex={i}
                  onFeedback={(rating) => submitFeedback(i, rating)}
                  onQuestionClick={(q) => sendMessage(q)}
                />
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Typing Indicator */}
        <AnimatePresence>
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <ChatBubble role="ai" content="" isTyping={true} />
            </motion.div>
          )}
        </AnimatePresence>

        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSend={handleSend} />
    </div>

  )
}
