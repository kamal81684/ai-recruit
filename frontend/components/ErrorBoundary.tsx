/**
 * Error Boundary Component
 *
 * React Error Boundary that catches JavaScript errors anywhere in the component tree,
 * logs those errors, and displays a fallback UI instead of the component tree that crashed.
 *
 * Features:
 * - Catches JavaScript errors in component tree
 * - Logs errors to error reporting service
 * - Provides user-friendly error messages
 * - Offers recovery options (retry, go back, go home)
 * - Captures error context and component stack
 * - Development vs production mode handling
 *
 * Usage:
 *   <ErrorBoundary fallback={<CustomError />}>
 *     <YourComponent />
 *   </ErrorBoundary>
 *
 * Contributor: shubham21155102
 */

"use client";

import { Component, ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode | ((error: Error, errorInfo: { componentStack: string }) => ReactNode);
  onError?: (error: Error, errorInfo: { componentStack: string }) => void;
  isolate?: boolean; // If true, only isolates the error boundary section
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: { componentStack: string } | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: { componentStack: string }): void {
    // Log the error to the console in development
    if (process.env.NODE_ENV === "development") {
      console.error("ErrorBoundary caught an error:", error);
      console.error("Component stack:", errorInfo.componentStack);
    }

    // Store error info in state
    this.setState({
      errorInfo,
    });

    // Call the onError callback if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log to error reporting service (Sentry, LogRocket, etc.)
    this.logErrorToService(error, errorInfo);
  }

  private logErrorToService(error: Error, errorInfo: { componentStack: string }): void {
    // In production, send to error tracking service
    if (typeof window !== "undefined" && process.env.NODE_ENV === "production") {
      // Example: Send to your error tracking service
      // Sentry.captureException(error, { contexts: { react: { componentStack: errorInfo.componentStack } } });

      // Console fallback for now
      console.error("Error logged:", {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href,
      });
    }
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    const { hasError, error, errorInfo } = this.state;
    const { children, fallback, isolate } = this.props;

    if (!hasError) {
      return children;
    }

    // Use custom fallback if provided
    if (fallback) {
      if (typeof fallback === "function") {
        return fallback(error!, errorInfo!);
      }
      return fallback;
    }

    // Default error UI
    return (
      <div className={`${isolate ? "" : "fixed inset-0 z-50"} flex items-center justify-center bg-slate-50 px-4`}>
        <div className="max-w-md w-full">
          <ErrorCard
            error={error!}
            onReset={this.handleReset}
            onReload={this.handleReload}
          />
        </div>
      </div>
    );
  }
}

interface ErrorCardProps {
  error: Error;
  onReset: () => void;
  onReload: () => void;
}

function ErrorCard({ error, onReset, onReload }: ErrorCardProps) {
  const isDevelopment = process.env.NODE_ENV === "development";

  return (
    <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
      {/* Error Icon Header */}
      <div className="bg-gradient-to-r from-red-50 to-orange-50 px-6 py-8 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-full shadow-sm mb-4">
          <span className="material-symbols-outlined text-4xl text-red-500">error_outline</span>
        </div>
        <h1 className="text-2xl font-bold text-slate-900 mb-2">Something went wrong</h1>
        <p className="text-slate-600">
          We encountered an unexpected error. Don&apos;t worry, your work is safe.
        </p>
      </div>

      {/* Error Details */}
      <div className="px-6 py-4">
        <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
          <p className="text-sm font-medium text-slate-700 mb-1">Error message:</p>
          <p className="text-sm text-slate-600 font-mono">{error.message}</p>
        </div>

        {/* Show stack trace in development */}
        {isDevelopment && error.stack && (
          <details className="mt-4">
            <summary className="text-sm font-medium text-slate-700 cursor-pointer hover:text-slate-900">
              View technical details
            </summary>
            <pre className="mt-2 text-xs bg-slate-900 text-slate-100 p-3 rounded-lg overflow-x-auto">
              {error.stack}
            </pre>
          </details>
        )}
      </div>

      {/* Action Buttons */}
      <div className="px-6 py-4 bg-slate-50 flex flex-col sm:flex-row gap-3">
        <button
          onClick={onReset}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-white rounded-lg font-semibold hover:bg-primary/90 transition-colors shadow-sm"
        >
          <span className="material-symbols-outlined text-lg">refresh</span>
          Try Again
        </button>
        <button
          onClick={onReload}
          className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-white border border-slate-300 text-slate-700 rounded-lg font-semibold hover:bg-slate-50 transition-colors"
        >
          <span className="material-symbols-outlined text-lg">home</span>
          Go to Dashboard
        </button>
      </div>

      {/* Support Links */}
      <div className="px-6 py-4 border-t border-slate-100">
        <p className="text-xs text-slate-500 text-center">
          Need help? <a href="mailto:support@example.com" className="text-primary hover:underline">Contact Support</a>
          {" "}or <a href="#" className="text-primary hover:underline">Report an Issue</a>
        </p>
      </div>
    </div>
  );
}

// Hook version for functional components
interface UseErrorBoundaryReturn {
  ErrorBoundary: typeof ErrorBoundary;
  triggerError: (error: Error) => never;
}

export function useErrorBoundary(): UseErrorBoundaryReturn {
  const triggerError = (error: Error) => {
    throw error;
  };

  return {
    ErrorBoundary,
    triggerError,
  };
}

// Inline error fallback component
export function InlineErrorFallback({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <span className="material-symbols-outlined text-red-500 text-xl mt-0.5">error</span>
        <div className="flex-1">
          <p className="text-sm font-semibold text-red-900">Something went wrong</p>
          <p className="text-xs text-red-700 mt-1">{error.message}</p>
          <button
            onClick={reset}
            className="mt-2 text-xs font-medium text-red-800 hover:text-red-900 underline"
          >
            Try again
          </button>
        </div>
      </div>
    </div>
  );
}

// HOC version for class components or wrapping existing components
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  fallback?: ReactNode
) {
  return function WithErrorBoundaryWrapper(props: P) {
    return (
      <ErrorBoundary fallback={fallback}>
        <WrappedComponent {...props} />
      </ErrorBoundary>
    );
  };
}
