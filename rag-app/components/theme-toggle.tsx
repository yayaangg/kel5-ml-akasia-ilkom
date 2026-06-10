"use client"

/**
 * ThemeToggle - AKASIA v2.4
 * Toggle button for dark/light mode
 */

import * as React from "react"
import { Sun, Moon } from "lucide-react"
import { motion } from "framer-motion"

// Safe theme hook that returns null if not in provider
function useSafeTheme() {
    const [theme, setTheme] = React.useState<"dark" | "light">("dark")
    const [mounted, setMounted] = React.useState(false)

    React.useEffect(() => {
        setMounted(true)
        const saved = localStorage.getItem("akasia-theme") as "dark" | "light"
        if (saved) {
            setTheme(saved)
        }
    }, [])

    const toggleTheme = () => {
        const newTheme = theme === "dark" ? "light" : "dark"
        setTheme(newTheme)
        localStorage.setItem("akasia-theme", newTheme)
        document.documentElement.classList.toggle("light", newTheme === "light")
    }

    return { theme, toggleTheme, mounted }
}

export function ThemeToggle() {
    const { theme, toggleTheme, mounted } = useSafeTheme()

    if (!mounted) {
        return (
            <div className="flex items-center gap-2 w-full p-3 rounded-xl text-sm font-medium bg-slate-800/50 text-slate-500 border border-slate-700/50">
                <Moon className="w-4 h-4" />
                <span>Loading...</span>
            </div>
        )
    }

    return (
        <motion.button
            onClick={toggleTheme}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center gap-2 w-full p-3 rounded-xl text-sm font-medium transition-colors bg-slate-800/50 hover:bg-slate-700/50 text-slate-300 hover:text-white border border-slate-700/50"
        >
            {theme === "dark" ? (
                <>
                    <Sun className="w-4 h-4 text-amber-400" />
                    <span>Light Mode</span>
                </>
            ) : (
                <>
                    <Moon className="w-4 h-4 text-blue-400" />
                    <span>Dark Mode</span>
                </>
            )}
        </motion.button>
    )
}

