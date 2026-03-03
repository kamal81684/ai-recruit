/**
 * Responsive Design Hooks
 *
 * Custom hooks for responsive design with:
 * - Breakpoint detection
 * - Media query matching
 * - Orientation detection
 * - Reduced motion preference
 * - High contrast mode detection
 *
 * Contributor: shubham21155102 - Code Quality & UX Improvements Phase 9
 */

"use client";

import { useEffect, useState, useCallback, type ReactNode } from "react";

// =============================================================================
// Breakpoints (matching Tailwind CSS defaults)
// =============================================================================

export const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  "2xl": 1536,
} as const;

export type Breakpoint = keyof typeof breakpoints;

// =============================================================================
// Media Query Hook
// =============================================================================

/**
 * Hook that listens to a media query and returns whether it matches
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    if (typeof window === "undefined") return;

    const mediaQuery = window.matchMedia(query);
    const handleChange = (e: MediaQueryListEvent) => {
      setMatches(e.matches);
    };

    // Modern browsers
    mediaQuery.addEventListener("change", handleChange);

    // Initial value
    setMatches(mediaQuery.matches);

    return () => {
      mediaQuery.removeEventListener("change", handleChange);
    };
  }, [query]);

  return matches;
}

// =============================================================================
// Breakpoint Hooks
// =============================================================================

/**
 * Returns true if the screen is at least the specified breakpoint
 */
export function useMinBreakpoint(breakpoint: Breakpoint): boolean {
  return useMediaQuery(`(min-width: ${breakpoints[breakpoint]}px)`);
}

/**
 * Returns true if the screen is smaller than the specified breakpoint
 */
export function useMaxBreakpoint(breakpoint: Breakpoint): boolean {
  return useMediaQuery(`(max-width: ${breakpoints[breakpoint] - 1}px)`);
}

/**
 * Returns the current breakpoint as a string
 */
export function useBreakpoint(): Breakpoint {
  const isXl = useMinBreakpoint("xl");
  const isLg = useMinBreakpoint("lg");
  const isMd = useMinBreakpoint("md");
  const isSm = useMinBreakpoint("sm");

  if (isXl) return "xl";
  if (isLg) return "lg";
  if (isMd) return "md";
  if (isSm) return "sm";
  return "2xl";
}

/**
 * Returns an object with all breakpoint states
 */
export function useBreakpoints() {
  return {
    isSm: useMinBreakpoint("sm"),
    isMd: useMinBreakpoint("md"),
    isLg: useMinBreakpoint("lg"),
    isXl: useMinBreakpoint("xl"),
    is2Xl: useMinBreakpoint("2xl"),
    current: useBreakpoint(),
  };
}

// =============================================================================
// Orientation & Device Hooks
// =============================================================================

/**
 * Returns the current orientation of the device
 */
export function useOrientation(): "portrait" | "landscape" {
  const isPortrait = useMediaQuery("(orientation: portrait)");
  return isPortrait ? "portrait" : "landscape";
}

/**
 * Returns true if the device is in portrait mode
 */
export function useIsPortrait(): boolean {
  return useOrientation() === "portrait";
}

/**
 * Returns true if the device is in landscape mode
 */
export function useIsLandscape(): boolean {
  return useOrientation() === "landscape";
}

// =============================================================================
// Accessibility Hooks
// =============================================================================

/**
 * Returns true if the user prefers reduced motion
 */
export function usePrefersReducedMotion(): boolean {
  return useMediaQuery("(prefers-reduced-motion: reduce)");
}

/**
 * Returns true if the user prefers high contrast
 */
export function usePrefersHighContrast(): boolean {
  return useMediaQuery("(prefers-contrast: high)");
}

/**
 * Returns true if the user prefers dark mode
 */
export function usePrefersDarkMode(): boolean {
  return useMediaQuery("(prefers-color-scheme: dark)");
}

/**
 * Returns true if the user prefers light mode
 */
export function usePrefersLightMode(): boolean {
  return useMediaQuery("(prefers-color-scheme: light)");
}

// =============================================================================
// Touch Device Detection
// =============================================================================

/**
 * Returns true if the device supports touch
 */
export function useIsTouchDevice(): boolean {
  return useMediaQuery("(hover: none) and (pointer: coarse)");
}

/**
 * Returns true if the device has a fine pointer (mouse)
 */
export function useHasFinePointer(): boolean {
  return useMediaQuery("(pointer: fine)");
}

// =============================================================================
// Screen Size Hook
// =============================================================================

/**
 * Returns the current screen dimensions
 */
export function useScreenSize() {
  const [size, setSize] = useState(() => {
    if (typeof window === "undefined") {
      return { width: 0, height: 0 };
    }
    return {
      width: window.innerWidth,
      height: window.innerHeight,
    };
  });

  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleResize = () => {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return size;
}

// =============================================================================
// Responsive Value Hook
// =============================================================================

/**
 * Returns a value based on the current breakpoint
 */
export function useResponsiveValue<T>(values: Partial<Record<Breakpoint, T>>, defaultValue: T): T {
  const bp = useBreakpoint();

  // Check breakpoints from largest to smallest
  for (const [key, value] of Object.entries(values)) {
    if (value !== undefined && breakpoints[key as Breakpoint] <= breakpoints[bp]) {
      return value;
    }
  }

  return defaultValue;
}

// =============================================================================
// Viewport Height Hook (fixes mobile browser issues)
// =============================================================================

/**
 * Returns the correct viewport height for mobile browsers
 * (fixes the issue where 100vh includes the address bar on mobile)
 */
export function useViewportHeight() {
  const [height, setHeight] = useState(0);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const updateHeight = () => {
      setHeight(window.visualViewport?.height ?? window.innerHeight);
    };

    updateHeight();
    window.visualViewport?.addEventListener("resize", updateHeight);
    window.addEventListener("resize", updateHeight);

    return () => {
      window.visualViewport?.removeEventListener("resize", updateHeight);
      window.removeEventListener("resize", updateHeight);
    };
  }, []);

  return height;
}

// =============================================================================
// Container Query Hook (simulated with ResizeObserver)
// =============================================================================

/**
 * Hook that tracks the size of a container element
 */
export function useContainerSize(ref: React.RefObject<HTMLElement>) {
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (!ref.current || typeof ResizeObserver === "undefined") return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setSize({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });

    observer.observe(ref.current);

    return () => observer.disconnect();
  }, [ref]);

  return size;
}

// =============================================================================
// Print Detection
// =============================================================================

/**
 * Returns true if the page is being printed
 */
export function useIsPrinting(): boolean {
  return useMediaQuery("print");
}

// =============================================================================
// Device Memory & Network (experimental)
// =============================================================================

/**
 * Returns the device memory in GB (if supported)
 */
export function useDeviceMemory(): number | null {
  const [memory, setMemory] = useState<number | null>(null);

  useEffect(() => {
    if ("deviceMemory" in navigator) {
      setMemory((navigator as any).deviceMemory);
    }
  }, []);

  return memory;
}

/**
 * Returns the effective connection type (if supported)
 */
export function useConnectionType(): "slow-2g" | "2g" | "3g" | "4g" | null {
  const [type, setType] = useState<"slow-2g" | "2g" | "3g" | "4g" | null>(null);

  useEffect(() => {
    if ("connection" in navigator) {
      const conn = (navigator as any).connection;
      setType(conn.effectiveType || null);

      const handleChange = () => {
        setType(conn.effectiveType || null);
      };

      conn.addEventListener("change", handleChange);
      return () => conn.removeEventListener("change", handleChange);
    }
  }, []);

  return type;
}

// =============================================================================
// Utility: Conditionally render based on breakpoint
// =============================================================================

interface ShowAtBreakpointProps {
  above?: Breakpoint;
  below?: Breakpoint;
  at?: Breakpoint;
  children: ReactNode;
}

/**
 * Component that conditionally renders children based on breakpoint
 */
export function ShowAtBreakpoint({ above, below, at, children }: ShowAtBreakpointProps) {
  const { isSm, isMd, isLg, isXl, is2Xl } = useBreakpoints();

  let shouldShow = true;

  if (above) {
    const check = { sm: isSm, md: isMd, lg: isLg, xl: isXl, "2xl": is2Xl };
    shouldShow = shouldShow && check[above];
  }

  if (below) {
    const check = { sm: isSm, md: isMd, lg: isLg, xl: isXl, "2xl": is2Xl };
    shouldShow = shouldShow && !check[below];
  }

  if (at) {
    const bp = useBreakpoint();
    shouldShow = shouldShow && bp === at;
  }

  return shouldShow ? <>{children}</> : null;
}
