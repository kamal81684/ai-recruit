/**
 * Accessible Layout Component
 *
 * Enhanced layout with:
 * - Skip-to-content links for keyboard users
 * - Proper heading hierarchy
 * - ARIA landmarks
 * - Focus management
 * - Screen reader announcements
 *
 * Contributor: shubham21155102 - Accessibility Improvements Phase 9
 */

"use client";

import { ReactNode, useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { MobileNavigation, BottomNavigation } from "@/components/ui/MobileNavigation";
import { ThemeToggle } from "@/contexts/ThemeContext";

interface NavItem {
  href: string;
  label: string;
  icon: string;
}

const navItems: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: "dashboard" },
  { href: "/candidates", label: "Candidates", icon: "people" },
  { href: "/jobs", label: "Job Posts", icon: "work" },
  { href: "/analytics", label: "Analytics", icon: "bar_chart" },
];

interface AccessibleLayoutProps {
  children: ReactNode;
  title?: string;
  description?: string;
}

/**
 * Skip link component for keyboard navigation
 */
function SkipLink({
  target,
  children,
}: {
  target: string;
  children: ReactNode;
}) {
  return (
    <a
      href={target}
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-white focus:rounded-lg focus:font-medium focus:shadow-lg"
    >
      {children}
    </a>
  );
}

/**
 * Main accessible layout wrapper
 */
export function AccessibleLayout({
  children,
  title = "AI Recruit",
  description = "AI-powered resume shortlisting assistant",
}: AccessibleLayoutProps) {
  const pathname = usePathname();
  const mainContentRef = useRef<HTMLElement>(null);

  // Announce page changes to screen readers
  useEffect(() => {
    const announcement = document.createElement("div");
    announcement.setAttribute("role", "status");
    announcement.setAttribute("aria-live", "polite");
    announcement.setAttribute("aria-atomic", "true");
    announcement.className = "sr-only";
    announcement.textContent = `Navigated to ${pathname}`;

    document.body.appendChild(announcement);
    setTimeout(() => document.body.removeChild(announcement), 1000);
  }, [pathname]);

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      {/* Skip Links for Keyboard Navigation */}
      <SkipLink target="#main-content">Skip to main content</SkipLink>
      <SkipLink target="#navigation">Skip to navigation</SkipLink>

      {/* Header */}
      <header className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:supports-[backdrop-filter]:bg-slate-900/60">
        <div className="flex h-16 items-center px-4 lg:px-6">
          <div className="flex flex-1 items-center gap-8">
            {/* Logo */}
            <a
              href="/"
              className="flex items-center gap-3 font-bold text-xl"
              aria-label="AI Recruit - Home"
            >
              <div className="size-8 bg-primary rounded-lg flex items-center justify-center text-white">
                <span className="material-symbols-outlined" aria-hidden="true">
                  cognition
                </span>
              </div>
              <span className="hidden sm:inline">AI Recruit</span>
            </a>

            {/* Desktop Navigation */}
            <nav
              id="navigation"
              className="hidden lg:flex items-center gap-6"
              aria-label="Main navigation"
            >
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <a
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-primary/10 text-primary"
                        : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800"
                    }`}
                    aria-current={isActive ? "page" : undefined}
                  >
                    <span
                      className="material-symbols-outlined text-lg"
                      aria-hidden="true"
                    >
                      {item.icon}
                    </span>
                    {item.label}
                  </a>
                );
              })}
            </nav>
          </div>

          {/* Right side actions */}
          <div className="flex items-center gap-2">
            {/* Theme Toggle */}
            <ThemeToggle />

            {/* User Menu */}
            <div className="hidden sm:block relative group">
              <button
                className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                aria-label="User menu"
                aria-expanded="false"
                aria-haspopup="true"
              >
                <div
                  className="size-8 rounded-full bg-cover bg-center border-2 border-slate-200 dark:border-slate-700"
                  style={{
                    backgroundImage:
                      'url("https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=100&h=100")',
                  }}
                  aria-hidden="true"
                />
                <span className="material-symbols-outlined text-slate-500">
                  expand_more
                </span>
              </button>
            </div>

            {/* Mobile Navigation Toggle */}
            <MobileNavigation />
          </div>
        </div>
      </header>

      {/* Breadcrumbs */}
      {pathname !== "/" && (
        <nav
          className="flex items-center gap-2 px-4 lg:px-6 py-3 text-sm border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50"
          aria-label="Breadcrumb"
        >
          <ol className="flex items-center gap-2">
            <li>
              <a
                href="/"
                className="text-slate-500 dark:text-slate-400 hover:text-primary dark:hover:text-primary transition-colors"
              >
                Home
              </a>
            </li>
            {pathname.split("/").filter(Boolean).map((segment, index, array) => {
              const href = "/" + array.slice(0, index + 1).join("/");
              const isLast = index === array.length - 1;
              return (
                <li key={href} className="flex items-center gap-2">
                  <span
                    className="material-symbols-outlined text-slate-400 text-sm"
                    aria-hidden="true"
                  >
                    chevron_right
                  </span>
                  {isLast ? (
                    <span
                      className="text-slate-900 dark:text-slate-100 font-medium"
                      aria-current="page"
                    >
                      {segment.charAt(0).toUpperCase() + segment.slice(1)}
                    </span>
                  ) : (
                    <a
                      href={href}
                      className="text-slate-500 dark:text-slate-400 hover:text-primary dark:hover:text-primary transition-colors"
                    >
                      {segment.charAt(0).toUpperCase() + segment.slice(1)}
                    </a>
                  )}
                </li>
              );
            })}
          </ol>
        </nav>
      )}

      {/* Main Content */}
      <main
        id="main-content"
        ref={mainContentRef}
        tabIndex={-1}
        className="flex-1"
        aria-label={`${title} - ${description}`}
      >
        {children}
      </main>

      {/* Bottom Navigation for Mobile */}
      <BottomNavigation className="lg:hidden" />

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 mt-auto">
        <div className="px-4 lg:px-6 py-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* Brand */}
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="size-8 bg-primary rounded-lg flex items-center justify-center text-white">
                  <span className="material-symbols-outlined">cognition</span>
                </div>
                <span className="font-bold text-lg">AI Recruit</span>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 max-w-md">
                {description}
              </p>
            </div>

            {/* Links */}
            <nav aria-label="Footer navigation">
              <h3 className="font-semibold mb-3 text-sm">Product</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <a
                    href="/features"
                    className="text-slate-600 dark:text-slate-400 hover:text-primary dark:hover:text-primary transition-colors"
                  >
                    Features
                  </a>
                </li>
                <li>
                  <a
                    href="/pricing"
                    className="text-slate-600 dark:text-slate-400 hover:text-primary dark:hover:text-primary transition-colors"
                  >
                    Pricing
                  </a>
                </li>
                <li>
                  <a
                    href="/docs"
                    className="text-slate-600 dark:text-slate-400 hover:text-primary dark:hover:text-primary transition-colors"
                  >
                    Documentation
                  </a>
                </li>
              </ul>
            </nav>

            <nav aria-label="Support navigation">
              <h3 className="font-semibold mb-3 text-sm">Support</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <a
                    href="/help"
                    className="text-slate-600 dark:text-slate-400 hover:text-primary dark:hover:text-primary transition-colors"
                  >
                    Help Center
                  </a>
                </li>
                <li>
                  <a
                    href="/privacy"
                    className="text-slate-600 dark:text-slate-400 hover:text-primary dark:hover:text-primary transition-colors"
                  >
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a
                    href="/status"
                    className="text-slate-600 dark:text-slate-400 hover:text-primary dark:hover:text-primary transition-colors"
                  >
                    System Status
                  </a>
                </li>
              </ul>
            </nav>
          </div>

          <div className="mt-8 pt-8 border-t border-slate-200 dark:border-slate-800 text-sm text-slate-500 dark:text-slate-400">
            <p>&copy; {new Date().getFullYear()} AI Recruit. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default AccessibleLayout;
