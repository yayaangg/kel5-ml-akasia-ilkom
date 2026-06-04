"use client"

/**
 * ThemeProvider - AKASIA
 * Dark/Light mode toggle dengan persistence
 */

import * as React from "react"

type Theme = "dark" | "light"

interface ThemeContextType {
    theme: Theme
    toggleTheme: () => void
}

const ThemeContext = React.createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
    const [theme, setTheme] = React.useState<Theme>("dark")
    const [mounted, setMounted] = React.useState(false)

    // Load saved theme on mount
    React.useEffect(() => {
        setMounted(true)
        const saved = localStorage.getItem("akasia-theme") as Theme
        if (saved) {
            setTheme(saved)
            document.documentElement.classList.toggle("light", saved === "light")
        }
    }, [])

    const toggleTheme = () => {
        const newTheme = theme === "dark" ? "light" : "dark"
        setTheme(newTheme)
        localStorage.setItem("akasia-theme", newTheme)
        document.documentElement.classList.toggle("light", newTheme === "light")
    }

    // Prevent hydration mismatch
    if (!mounted) {
        return <>{children}</>
    }

    return (
        <ThemeContext.Provider value={{ theme, toggleTheme }}>
            {children}
        </ThemeContext.Provider>
    )
}

export function useTheme() {
    const context = React.useContext(ThemeContext)
    if (context === undefined) {
        throw new Error("useTheme must be used within a ThemeProvider")
    }
    return context
}
