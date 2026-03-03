/**
 * Root Layout with Enhanced Accessibility and Features
 *
 * Integrates:
 * - Theme provider with dark mode support
 * - Toast notification system
 * - Error boundaries
 * - Accessibility features
 * - Performance optimizations
 *
 * Contributor: shubham21155102 - Code Quality & UX Improvements Phase 9
 */

import type { Metadata } from "next";
import { Geist, Geist_Mono, Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider, initializeDarkModeStyles } from "@/contexts/ThemeContext";
import { ToastProvider } from "@/components/ui/Toast";
import { ErrorBoundary } from "@/components/ErrorBoundary";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const inter = Inter({
  variable: "--font-display",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Recruit - AI-Powered Resume Shortlisting Assistant",
  description: "Streamline your hiring process with AI-powered resume analysis, candidate evaluation, and intelligent job matching.",
  keywords: ["AI recruitment", "resume screening", "candidate evaluation", "hiring automation", "HR technology"],
  authors: [{ name: "AI Recruit Team" }],
  openGraph: {
    title: "AI Recruit - AI-Powered Resume Shortlisting Assistant",
    description: "Streamline your hiring process with AI-powered resume analysis",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Initialize dark mode styles and accessibility features
  if (typeof window !== "undefined") {
    initializeDarkModeStyles();
  }

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght@100..700,0..1&display=swap" />
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" />
        <meta name="theme-color" content="#135bec" />
        <meta name="color-scheme" content="light dark" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${inter.variable} bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-display antialiased`}
      >
        <ErrorBoundary>
          <ThemeProvider>
            <ToastProvider>
              {children}
            </ToastProvider>
          </ThemeProvider>
        </ErrorBoundary>

      </body>
    </html>
  );
}
