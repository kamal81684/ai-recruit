/**
 * Mobile Navigation Component
 *
 * Responsive navigation component for mobile devices with:
 * - Smooth slide-in animation
 * - Keyboard navigation support
 * - ARIA labels for accessibility
 * - Touch-friendly interactions
 * - Focus trap when menu is open
 *
 * Contributor: shubham21155102 - Code Quality & UX Improvements Phase 9
 */

"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

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

interface MobileNavigationProps {
  className?: string;
}

export function MobileNavigation({ className = "" }: MobileNavigationProps) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const firstFocusRef = useRef<HTMLButtonElement>(null);
  const lastFocusRef = useRef<HTMLAnchorElement>(null);

  // Handle escape key to close menu
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      // Prevent body scroll when menu is open
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  // Focus trap when menu is open
  useEffect(() => {
    if (!isOpen) return;

    const focusableElements = menuRef.current?.querySelectorAll<
      HTMLAnchorElement | HTMLButtonElement
    >(
      'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements && focusableElements.length > 0) {
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      const handleTab = (e: KeyboardEvent) => {
        if (e.key !== "Tab") return;

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      };

      document.addEventListener("keydown", handleTab);

      // Focus first element when menu opens
      firstElement.focus();

      return () => {
        document.removeEventListener("keydown", handleTab);
      };
    }
  }, [isOpen]);

  const toggleMenu = () => {
    setIsOpen((prev) => !prev);
  };

  const closeMenu = () => {
    setIsOpen(false);
  };

  return (
    <div className={`lg:hidden ${className}`}>
      {/* Hamburger Menu Button */}
      <button
        ref={firstFocusRef}
        type="button"
        onClick={toggleMenu}
        className="relative inline-flex items-center justify-center p-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors group"
        aria-expanded={isOpen}
        aria-controls="mobile-menu"
        aria-label={isOpen ? "Close navigation menu" : "Open navigation menu"}
      >
        <span className="sr-only">
          {isOpen ? "Close menu" : "Open menu"}
        </span>
        <div className="flex flex-col gap-1.5">
          <span
            className={`block w-6 h-0.5 bg-slate-700 dark:bg-slate-300 transition-all duration-300 ${
              isOpen ? "rotate-45 translate-y-2" : ""
            }`}
            aria-hidden="true"
          />
          <span
            className={`block w-6 h-0.5 bg-slate-700 dark:bg-slate-300 transition-all duration-300 ${
              isOpen ? "opacity-0" : ""
            }`}
            aria-hidden="true"
          />
          <span
            className={`block w-6 h-0.5 bg-slate-700 dark:bg-slate-300 transition-all duration-300 ${
              isOpen ? "-rotate-45 -translate-y-2" : ""
            }`}
            aria-hidden="true"
          />
        </div>
      </button>

      {/* Mobile Menu Overlay */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 z-40 transition-opacity duration-300"
            onClick={closeMenu}
            aria-hidden="true"
          />

          {/* Mobile Menu Panel */}
          <div
            ref={menuRef}
            id="mobile-menu"
            className="fixed top-0 right-0 bottom-0 w-80 max-w-[85vw] bg-white dark:bg-slate-900 shadow-2xl z-50 transform transition-transform duration-300 ease-out"
            role="dialog"
            aria-modal="true"
            aria-label="Main navigation"
          >
            {/* Menu Header */}
            <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-3">
                <div className="size-10 bg-primary rounded-lg flex items-center justify-center text-white">
                  <span className="material-symbols-outlined">cognition</span>
                </div>
                <span className="text-lg font-bold text-slate-900 dark:text-slate-100">
                  AI Recruit
                </span>
              </div>
              <button
                type="button"
                onClick={closeMenu}
                className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                aria-label="Close menu"
              >
                <span className="material-symbols-outlined text-slate-600 dark:text-slate-400">
                  close
                </span>
              </button>
            </div>

            {/* Navigation Links */}
            <nav
              className="p-4"
              aria-label="Mobile navigation"
            >
              <ul className="space-y-2" role="menubar">
                {navItems.map((item) => (
                  <li key={item.href} role="none">
                    <Link
                      href={item.href}
                      ref={item.href === "/analytics" ? lastFocusRef : undefined}
                      onClick={closeMenu}
                      role="menuitem"
                      className="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors font-medium"
                    >
                      <span
                        className="material-symbols-outlined text-slate-500"
                        aria-hidden="true"
                      >
                        {item.icon}
                      </span>
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>

            {/* Menu Footer */}
            <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
              <div className="flex items-center gap-3">
                <div
                  className="size-10 rounded-full bg-cover bg-center border-2 border-white dark:border-slate-600 shadow-sm"
                  style={{
                    backgroundImage:
                      'url("https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=100&h=100")',
                  }}
                  aria-hidden="true"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">
                    Demo User
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                    demo@airecruit.com
                  </p>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/**
 * Bottom Navigation Bar for Mobile
 * Alternative to hamburger menu - shows navigation at bottom of screen
 */
export function BottomNavigation({ className = "" }: { className?: string }) {
  const pathname =
    typeof window !== "undefined" ? window.location.pathname : "/";

  return (
    <nav
      className={`lg:hidden fixed bottom-0 left-0 right-0 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 z-30 safe-area-bottom ${className}`}
      aria-label="Bottom navigation"
    >
      <ul className="flex items-center justify-around h-16" role="menubar">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <li key={item.href} className="flex-1" role="none">
              <Link
                href={item.href}
                role="menuitem"
                className={`flex flex-col items-center justify-center h-full gap-1 transition-colors ${
                  isActive
                    ? "text-primary"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
                }`}
                aria-current={isActive ? "page" : undefined}
              >
                <span
                  className="material-symbols-outlined text-xl"
                  aria-hidden="true"
                >
                  {item.icon}
                </span>
                <span className="text-[10px] font-medium leading-tight">
                  {item.label}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

export default MobileNavigation;
