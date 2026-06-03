"use client"

/**
 * StatsCard Component - AKASIA v2.0
 * Kartu statistik dengan animasi counter
 */

import * as React from "react"
import { motion, useSpring, useTransform } from "framer-motion"
import { GlassCard } from "@/components/ui/glass-card"
import { LucideIcon } from "lucide-react"

interface StatsCardProps {
    title: string
    value: string | number
    change: string
    icon: LucideIcon
    trend?: 'up' | 'down' | 'neutral'
    color?: 'blue' | 'purple' | 'cyan' | 'green'
}

// Animated number counter
function AnimatedNumber({ value }: { value: number }) {
    const spring = useSpring(0, { stiffness: 100, damping: 30 })
    const display = useTransform(spring, (current) => Math.round(current))
    const [displayValue, setDisplayValue] = React.useState(0)

    React.useEffect(() => {
        spring.set(value)
    }, [spring, value])

    React.useEffect(() => {
        return display.on("change", (v) => setDisplayValue(v))
    }, [display])

    return <span>{displayValue}</span>
}

export function StatsCard({
    title,
    value,
    change,
    icon: Icon,
    trend = 'neutral',
    color = 'purple'
}: StatsCardProps) {
    const colorClasses = {
        blue: 'from-blue-500/20 to-cyan-500/20 text-blue-400',
        purple: 'from-purple-500/20 to-pink-500/20 text-purple-400',
        cyan: 'from-cyan-500/20 to-blue-500/20 text-cyan-400',
        green: 'from-green-500/20 to-emerald-500/20 text-green-400'
    }

    const numericValue = typeof value === 'string' ? parseInt(value.replace(/[^0-9]/g, '')) || 0 : value
    const isNumeric = !isNaN(numericValue) && typeof value !== 'string' || /^\d+$/.test(value as string)

    return (
        <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
        >
            <GlassCard className="p-6 relative overflow-hidden group">
                {/* Background Glow */}
                <motion.div
                    className={`absolute -top-10 -right-10 w-32 h-32 rounded-full bg-gradient-to-br ${colorClasses[color]} blur-2xl opacity-30 group-hover:opacity-50 transition-opacity`}
                />

                <div className="relative flex justify-between items-start">
                    <div className="flex-1">
                        <p className="text-sm font-medium text-slate-400">{title}</p>
                        <h3 className="text-3xl font-bold mt-2 text-white">
                            {isNumeric ? (
                                <AnimatedNumber value={numericValue} />
                            ) : (
                                value
                            )}
                        </h3>
                        <motion.p
                            className={`text-xs mt-2 flex items-center gap-1 ${trend === 'up' ? 'text-green-400' :
                                    trend === 'down' ? 'text-red-400' : 'text-slate-500'
                                }`}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.3 }}
                        >
                            {trend === 'up' && '↑'}
                            {trend === 'down' && '↓'}
                            {change}
                        </motion.p>
                    </div>
                    <motion.div
                        className={`p-3 rounded-xl bg-gradient-to-br ${colorClasses[color]} border border-white/10`}
                        whileHover={{ scale: 1.1, rotate: 5 }}
                        transition={{ type: "spring", stiffness: 400 }}
                    >
                        <Icon className="w-6 h-6" />
                    </motion.div>
                </div>
            </GlassCard>
        </motion.div>
    )
}