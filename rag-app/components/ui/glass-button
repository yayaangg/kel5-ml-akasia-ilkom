"use client"

import * as React from "react"
import { motion, HTMLMotionProps } from "framer-motion"
import { cn } from "@/lib/utils"

interface GlassButtonProps extends HTMLMotionProps<"button"> {
    children: React.ReactNode
    variant?: "primary" | "secondary" | "danger" | "ghost"
    size?: "sm" | "md" | "lg"
}

export function GlassButton({
    children,
    className,
    variant = "primary",
    size = "md",
    ...props
}: GlassButtonProps) {
    const variants = {
        primary: "bg-blue-600/20 border-blue-500/30 hover:bg-blue-600/40 text-blue-100",
        secondary: "bg-white/5 border-white/10 hover:bg-white/10 text-slate-200",
        danger: "bg-red-500/10 border-red-500/20 hover:bg-red-500/20 text-red-200",
        ghost: "bg-transparent border-transparent hover:bg-white/5 text-slate-300",
    }

    const sizes = {
        sm: "px-3 py-1.5 text-sm",
        md: "px-4 py-2",
        lg: "px-6 py-3 text-lg",
    }

    return (
        <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className={cn(
                "relative rounded-lg border backdrop-blur-sm font-medium transition-all flex items-center justify-center gap-2",
                variants[variant],
                sizes[size],
                className
            )}
            {...props}
        >
            {children}
        </motion.button>
    )
}
