/**
 * Toast Notification System
 *
 * Provides non-intrusive user feedback with:
 * - Multiple toast variants (success, error, warning, info)
 * - Auto-dismiss with configurable duration
 * - Stack animation for multiple toasts
 * - Keyboard dismissible (Escape key)
 * - Screen reader announcements
 * - Customizable position
 *
 * Contributor: shubham21155102 - Code Quality & UX Improvements Phase 9
 */

"use client";

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from "react";
import { useAnnouncer } from "@/contexts/ThemeContext";

// =============================================================================
// Types
// =============================================================================

export type ToastVariant = "success" | "error" | "warning" | "info";
export type ToastPosition = "top-right" | "top-left" | "bottom-right" | "bottom-left" | "top-center" | "bottom-center";

export interface Toast {
  id: string;
  variant: ToastVariant;
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
  dismissible?: boolean;
}

interface ToastContextValue {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

// =============================================================================
// Context
// =============================================================================

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}

// =============================================================================
// Provider
// =============================================================================

interface ToastProviderProps {
  children: ReactNode;
  position?: ToastPosition;
  maxToasts?: number;
}

export function ToastProvider({
  children,
  position = "bottom-right",
  maxToasts = 5,
}: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const { announce } = useAnnouncer();

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const addToast = useCallback(
    (toast: Omit<Toast, "id">) => {
      const id = Math.random().toString(36).substring(2, 9);
      const newToast: Toast = {
        ...toast,
        id,
        duration: toast.duration ?? 5000,
        dismissible: toast.dismissible ?? true,
      };

      setToasts((prev) => {
        const updated = [newToast, ...prev];
        return updated.slice(0, maxToasts);
      });

      // Announce to screen readers
      announce(`${newToast.variant}: ${newToast.title}${newToast.message ? `. ${newToast.message}` : ""}`);

      // Auto-dismiss
      if (newToast.duration && newToast.duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, newToast.duration);
      }

      return id;
    },
    [maxToasts, removeToast, announce]
  );

  const clearToasts = useCallback(() => {
    setToasts([]);
  }, []);

  // Handle escape key to dismiss all toasts
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && toasts.length > 0) {
        clearToasts();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [toasts, clearToasts]);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, clearToasts }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} position={position} />
    </ToastContext.Provider>
  );
}

// =============================================================================
// Toast Container
// =============================================================================

interface ToastContainerProps {
  toasts: Toast[];
  onRemove: (id: string) => void;
  position: ToastPosition;
}

function ToastContainer({ toasts, onRemove, position }: ToastContainerProps) {
  if (toasts.length === 0) return null;

  const positionClasses: Record<ToastPosition, string> = {
    "top-right": "top-4 right-4",
    "top-left": "top-4 left-4",
    "bottom-right": "bottom-4 right-4",
    "bottom-left": "bottom-4 left-4",
    "top-center": "top-4 left-1/2 -translate-x-1/2",
    "bottom-center": "bottom-4 left-1/2 -translate-x-1/2",
  };

  return (
    <div
      className={`fixed z-50 flex flex-col gap-3 pointer-events-none ${positionClasses[position]}`}
      role="region"
      aria-label="Toast notifications"
      aria-live="polite"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
}

// =============================================================================
// Toast Item
// =============================================================================

interface ToastItemProps {
  toast: Toast;
  onRemove: (id: string) => void;
}

function ToastItem({ toast, onRemove }: ToastItemProps) {
  const [isExiting, setIsExiting] = useState(false);

  const handleDismiss = () => {
    setIsExiting(true);
    setTimeout(() => onRemove(toast.id), 300);
  };

  const variantConfig: Record<
    ToastVariant,
    { icon: string; bgClass: string; borderClass: string; iconClass: string; titleClass: string }
  > = {
    success: {
      icon: "check_circle",
      bgClass: "bg-green-50 dark:bg-green-900/20",
      borderClass: "border-green-200 dark:border-green-800",
      iconClass: "text-green-500",
      titleClass: "text-green-900 dark:text-green-100",
    },
    error: {
      icon: "error",
      bgClass: "bg-red-50 dark:bg-red-900/20",
      borderClass: "border-red-200 dark:border-red-800",
      iconClass: "text-red-500",
      titleClass: "text-red-900 dark:text-red-100",
    },
    warning: {
      icon: "warning",
      bgClass: "bg-amber-50 dark:bg-amber-900/20",
      borderClass: "border-amber-200 dark:border-amber-800",
      iconClass: "text-amber-500",
      titleClass: "text-amber-900 dark:text-amber-100",
    },
    info: {
      icon: "info",
      bgClass: "bg-blue-50 dark:bg-blue-900/20",
      borderClass: "border-blue-200 dark:border-blue-800",
      iconClass: "text-blue-500",
      titleClass: "text-blue-900 dark:text-blue-100",
    },
  };

  const config = variantConfig[toast.variant];

  return (
    <div
      className={`pointer-events-auto w-80 max-w-[calc(100vw-2rem)] ${config.bgClass} ${config.borderClass} border rounded-xl shadow-lg overflow-hidden transform transition-all duration-300 ${isExiting ? "opacity-0 translate-x-full" : "opacity-100 translate-x-0"}`}
      role="alert"
      aria-live={toast.variant === "error" ? "assertive" : "polite"}
      aria-atomic="true"
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          {/* Icon */}
          <span
            className={`material-symbols-outlined ${config.iconClass} text-xl flex-shrink-0 mt-0.5`}
            aria-hidden="true"
          >
            {config.icon}
          </span>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <h4 className={`text-sm font-semibold ${config.titleClass}`}>
              {toast.title}
            </h4>
            {toast.message && (
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                {toast.message}
              </p>
            )}
            {toast.action && (
              <button
                onClick={() => {
                  toast.action!.onClick();
                  handleDismiss();
                }}
                className="mt-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
              >
                {toast.action.label}
              </button>
            )}
          </div>

          {/* Dismiss Button */}
          {toast.dismissible && (
            <button
              onClick={handleDismiss}
              className="flex-shrink-0 p-1 rounded hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
              aria-label="Dismiss notification"
            >
              <span
                className="material-symbols-outlined text-slate-500 dark:text-slate-400 text-lg"
              >
                close
              </span>
            </button>
          )}
        </div>

        {/* Progress Bar (for auto-dismiss) */}
        {toast.duration && toast.duration > 0 && (
          <div className="mt-3 h-1 bg-black/10 dark:bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-current opacity-30 transition-all duration-100 ease-linear"
              style={{
                animation: `toast-progress ${toast.duration}ms linear forwards`,
              }}
            />
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes toast-progress {
          from {
            width: 100%;
          }
          to {
            width: 0%;
          }
        }
      `}</style>
    </div>
  );
}

// =============================================================================
// Convenience Hooks
// =============================================================================

export function useToastActions() {
  const { addToast } = useToast();

  return {
    success: (title: string, message?: string, options?: Partial<Omit<Toast, "id" | "variant" | "title" | "message">>) =>
      addToast({ variant: "success", title, message, ...options }),
    error: (title: string, message?: string, options?: Partial<Omit<Toast, "id" | "variant" | "title" | "message">>) =>
      addToast({ variant: "error", title, message, ...options }),
    warning: (title: string, message?: string, options?: Partial<Omit<Toast, "id" | "variant" | "title" | "message">>) =>
      addToast({ variant: "warning", title, message, ...options }),
    info: (title: string, message?: string, options?: Partial<Omit<Toast, "id" | "variant" | "title" | "message">>) =>
      addToast({ variant: "info", title, message, ...options }),
  };
}

export default ToastProvider;
