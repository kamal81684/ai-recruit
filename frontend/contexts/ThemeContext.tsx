"use client";

import { createContext, useContext, useEffect, useState } from "react";

type Theme = "light" | "dark" | "system";
type ColorScheme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  colorScheme: ColorScheme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const THEME_STORAGE_KEY = "ai-recruit-theme";

/**
 * Theme Provider - Handles dark mode, light mode, and system preference.
 *
 * Features:
 * - System preference detection
 * - Persistent theme storage
 * - Smooth transitions between themes
 * - WCAG AA compliant contrast ratios
 *
 * Contributor: shubham21155102 - Enterprise Architecture Phase 7
 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("system");
  const [colorScheme, setColorScheme] = useState<ColorScheme>("light");

  // Initialize theme from localStorage or system preference
  useEffect(() => {
    const stored = localStorage.getItem(THEME_STORAGE_KEY) as Theme | null;
    const initialTheme = stored || "system";
    setThemeState(initialTheme);
    updateColorScheme(initialTheme);
  }, []);

  // Update color scheme when theme changes
  useEffect(() => {
    updateColorScheme(theme);
  }, [theme]);

  // Listen for system theme changes
  useEffect(() => {
    if (theme !== "system") return;

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const handleChange = (e: MediaQueryListEvent) => {
      setColorScheme(e.matches ? "dark" : "light");
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [theme]);

  const updateColorScheme = (currentTheme: Theme) => {
    let scheme: ColorScheme = "light";

    if (currentTheme === "system") {
      scheme = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    } else {
      scheme = currentTheme;
    }

    setColorScheme(scheme);

    // Apply to document
    const root = document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.add(scheme);

    // Update meta color theme
    const metaTheme = document.querySelector('meta[name="theme-color"]');
    if (metaTheme) {
      metaTheme.setAttribute(
        "content",
        scheme === "dark" ? "#0f172a" : "#ffffff"
      );
    }
  };

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem(THEME_STORAGE_KEY, newTheme);
  };

  const toggleTheme = () => {
    if (theme === "light") {
      setTheme("dark");
    } else if (theme === "dark") {
      setTheme("system");
    } else {
      setTheme("light");
    }
  };

  return (
    <ThemeContext.Provider
      value={{ theme, colorScheme, setTheme, toggleTheme }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

/**
 * Hook to use theme context
 */
export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}

/**
 * Theme Toggle Button Component
 */
export function ThemeToggle() {
  const { theme, colorScheme, toggleTheme } = useTheme();

  const getIcon = () => {
    if (theme === "system") {
      return colorScheme === "dark" ? "dark_mode" : "light_mode";
    }
    return theme === "dark" ? "dark_mode" : "light_mode";
  };

  const getLabel = () => {
    if (theme === "system") {
      return `System (${colorScheme})`;
    }
    return theme.charAt(0).toUpperCase() + theme.slice(1);
  };

  return (
    <button
      onClick={toggleTheme}
      className="relative inline-flex items-center justify-center p-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors group"
      aria-label={`Toggle theme. Current: ${getLabel()}`}
      title={`Current theme: ${getLabel()}. Click to cycle through themes.`}
    >
      <span className="material-symbols-outlined text-slate-700 dark:text-slate-300 text-[20px]">
        {getIcon()}
      </span>
      <span className="sr-only">Toggle theme (current: {getLabel()})</span>
    </button>
  );
}

/**
 * Apply dark mode styles with proper CSS variables
 */
export function initializeDarkModeStyles() {
  if (typeof document === "undefined") return;

  const style = document.createElement("style");
  style.id = "dark-mode-styles";
  style.textContent = `
    /* Dark mode color variables - WCAG AA compliant */
    :root {
      --background-primary: #ffffff;
      --background-secondary: #f8fafc;
      --background-tertiary: #f1f5f9;
      --text-primary: #0f172a;
      --text-secondary: #475569;
      --text-tertiary: #94a3b8;
      --border-primary: #e2e8f0;
      --border-secondary: #cbd5e1;
      --accent-primary: #3b82f6;
      --accent-secondary: #2563eb;
      --success: #10b981;
      --warning: #f59e0b;
      --error: #ef4444;
    }

    .dark {
      --background-primary: #0f172a;
      --background-secondary: #1e293b;
      --background-tertiary: #334155;
      --text-primary: #f1f5f9;
      --text-secondary: #cbd5e1;
      --text-tertiary: #94a3b8;
      --border-primary: #334155;
      --border-secondary: #475569;
      --accent-primary: #60a5fa;
      --accent-secondary: #3b82f6;
    }

    /* Smooth transitions */
    *, *::before, *::after {
      transition-property: background-color, border-color, color, fill, stroke;
      transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
      transition-duration: 150ms;
    }

    /* Skip to content link for accessibility */
    .skip-to-content {
      position: absolute;
      left: -9999px;
      z-index: 999;
      padding: 1rem 2rem;
      background: var(--accent-primary);
      color: white;
      text-decoration: none;
      border-radius: 0.5rem;
    }

    .skip-to-content:focus {
      left: 1rem;
      top: 1rem;
    }

    /* Focus visible styles for keyboard navigation */
    :focus-visible {
      outline: 2px solid var(--accent-primary);
      outline-offset: 2px;
      border-radius: 0.25rem;
    }

    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        transition-duration: 0.01ms !important;
        animation-duration: 0.01ms !important;
      }
    }
  `;

  if (!document.getElementById("dark-mode-styles")) {
    document.head.appendChild(style);
  }
}

/**
 * High contrast mode support for accessibility
 */
export function useHighContrast() {
  const [isHighContrast, setIsHighContrast] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-contrast: high)");

    const handleChange = (e: MediaQueryListEvent) => {
      setIsHighContrast(e.matches);
    };

    setIsHighContrast(mediaQuery.matches);
    mediaQuery.addEventListener("change", handleChange);

    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  return isHighContrast;
}

/**
 * Reduced motion support for accessibility
 */
export function useReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    setPrefersReducedMotion(mediaQuery.matches);
    mediaQuery.addEventListener("change", handleChange);

    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  return prefersReducedMotion;
}

/**
 * Screen reader announcements for dynamic content
 */
export function useAnnouncer() {
  const announce = (message: string, priority: "polite" | "assertive" = "polite") => {
    const announcer = document.createElement("div");
    announcer.setAttribute("role", "status");
    announcer.setAttribute("aria-live", priority);
    announcer.setAttribute("aria-atomic", "true");
    announcer.className = "sr-only";
    announcer.textContent = message;

    document.body.appendChild(announcer);

    setTimeout(() => {
      document.body.removeChild(announcer);
    }, 1000);
  };

  return { announce };
}
