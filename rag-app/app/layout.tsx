import type { Metadata } from "next";
import { Inter, Roboto_Mono } from "next/font/google";
import "./globals.css";

const fontSans = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

const fontMono = Roboto_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "AKASIA v2.4 - Asisten Akademik UHO",
  description: "Asisten Akademik Berbasis AI untuk Universitas Halu Oleo",
};

import { ChatProvider } from "@/components/chat-provider";
import { ThemeProvider } from "@/components/theme-provider";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${fontSans.variable} ${fontMono.variable} antialiased aurora-bg min-h-screen`} suppressHydrationWarning>
        <ThemeProvider>
          <ChatProvider>
            {children}
          </ChatProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
