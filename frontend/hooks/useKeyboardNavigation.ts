/**
 * Keyboard Navigation Utilities
 *
 * Custom hooks and utilities for keyboard navigation with:
 * - Arrow key navigation
 * - Focus trapping
 * - Focus restoration
 * - Keyboard shortcuts
 * - Roving tabindex
 *
 * Contributor: shubham21155102 - Accessibility Improvements Phase 9
 */

"use client";

import { useEffect, useRef, useState, useCallback } from "react";

// =============================================================================
// Focus Trap Hook
// =============================================================================

/**
 * Hook to trap focus within a container
 * Useful for modals, dropdowns, and overlays
 */
export function useFocusTrap(isActive: boolean = true) {
  const containerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    const container = containerRef.current;
    const focusableElements = container.querySelectorAll<
      HTMLElement | SVGElement
    >(
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length === 0) return;

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

    // Focus first element when trap activates
    firstElement.focus();

    return () => {
      document.removeEventListener("keydown", handleTab);
    };
  }, [isActive]);

  return containerRef;
}

// =============================================================================
// Focus Restoration Hook
// =============================================================================

/**
 * Hook to save and restore focus
 * Useful for dialogs and menus
 */
export function useFocusRestore() {
  const previousFocusRef = useRef<HTMLElement | null>(null);

  const saveFocus = useCallback(() => {
    previousFocusRef.current = document.activeElement as HTMLElement;
  }, []);

  const restoreFocus = useCallback(() => {
    if (previousFocusRef.current) {
      previousFocusRef.current.focus();
    }
  }, []);

  return { saveFocus, restoreFocus };
}

// =============================================================================
// Keyboard Shortcuts Hook
// =============================================================================

type KeyboardShortcutHandler = (e: KeyboardEvent) => void;

interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  metaKey?: boolean;
  handler: KeyboardShortcutHandler;
  description?: string;
}

/**
 * Hook to register keyboard shortcuts
 */
export function useKeyboardShortcuts(
  shortcuts: KeyboardShortcut[],
  isActive: boolean = true
) {
  useEffect(() => {
    if (!isActive) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        const keyMatch = e.key === shortcut.key;
        const ctrlMatch = shortcut.ctrlKey === undefined || e.ctrlKey === shortcut.ctrlKey;
        const shiftMatch = shortcut.shiftKey === undefined || e.shiftKey === shortcut.shiftKey;
        const altMatch = shortcut.altKey === undefined || e.altKey === shortcut.altKey;
        const metaMatch = shortcut.metaKey === undefined || e.metaKey === shortcut.metaKey;

        if (keyMatch && ctrlMatch && shiftMatch && altMatch && metaMatch) {
          e.preventDefault();
          shortcut.handler(e);
          return;
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [shortcuts, isActive]);
}

// =============================================================================
// Arrow Key Navigation Hook
// =============================================================================

/**
 * Hook to add arrow key navigation to a list of items
 */
export function useArrowKeyNavigation(itemCount: number, options: {
  isActive?: boolean;
  loop?: boolean;
  orientation?: "horizontal" | "vertical" | "both";
  onSelect?: (index: number) => void;
} = {}) {
  const {
    isActive = true,
    loop = true,
    orientation = "vertical",
    onSelect,
  } = options;

  const [focusedIndex, setFocusedIndex] = useState(0);

  useEffect(() => {
    if (!isActive) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      let newIndex = focusedIndex;

      switch (e.key) {
        case "ArrowDown":
          if (orientation === "vertical" || orientation === "both") {
            e.preventDefault();
            newIndex = focusedIndex + 1;
            if (newIndex >= itemCount) {
              newIndex = loop ? 0 : itemCount - 1;
            }
          }
          break;
        case "ArrowUp":
          if (orientation === "vertical" || orientation === "both") {
            e.preventDefault();
            newIndex = focusedIndex - 1;
            if (newIndex < 0) {
              newIndex = loop ? itemCount - 1 : 0;
            }
          }
          break;
        case "ArrowRight":
          if (orientation === "horizontal" || orientation === "both") {
            e.preventDefault();
            newIndex = focusedIndex + 1;
            if (newIndex >= itemCount) {
              newIndex = loop ? 0 : itemCount - 1;
            }
          }
          break;
        case "ArrowLeft":
          if (orientation === "horizontal" || orientation === "both") {
            e.preventDefault();
            newIndex = focusedIndex - 1;
            if (newIndex < 0) {
              newIndex = loop ? itemCount - 1 : 0;
            }
          }
          break;
        case "Home":
          e.preventDefault();
          newIndex = 0;
          break;
        case "End":
          e.preventDefault();
          newIndex = itemCount - 1;
          break;
        case "Enter":
        case " ":
          if (onSelect && e.target instanceof HTMLElement && e.target.tagName !== "INPUT" && e.target.tagName !== "TEXTAREA") {
            e.preventDefault();
            onSelect(focusedIndex);
          }
          return;
        default:
          return;
      }

      setFocusedIndex(newIndex);

      // Focus the new item
      const items = document.querySelectorAll(`[data-nav-index]:not([aria-disabled="true"])`);
      const newFocusElement = items[newIndex] as HTMLElement;
      newFocusElement?.focus();
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [focusedIndex, itemCount, isActive, loop, orientation, onSelect]);

  return { focusedIndex, setFocusedIndex };
}

// =============================================================================
// Roving Tabindex Hook
// =============================================================================

/**
 * Hook to implement roving tabindex pattern
 * Allows arrow key navigation through a list while only one item is tabbable
 */
export function useRovingTabindex(itemCount: number) {
  const [activeIndex, setActiveIndex] = useState(0);

  const getTabindex = useCallback(
    (index: number) => (index === activeIndex ? 0 : -1),
    [activeIndex]
  );

  const getFocusableProps = useCallback(
    (index: number) => ({
      tabIndex: getTabindex(index),
      "data-nav-index": index,
      onFocus: () => setActiveIndex(index),
    }),
    [getTabindex]
  );

  return { activeIndex, getFocusableProps, setActiveIndex };
}

// =============================================================================
// Escape Key Hook
// =============================================================================

/**
 * Hook to listen for escape key
 */
export function useEscapeKey(handler: () => void, isActive: boolean = true) {
  useEffect(() => {
    if (!isActive) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        handler();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [handler, isActive]);
}

// =============================================================================
// Enter Key Hook
// =============================================================================

/**
 * Hook to listen for enter key
 */
export function useEnterKey(handler: () => void, isActive: boolean = true) {
  useEffect(() => {
    if (!isActive) return;

    const handleEnter = (e: KeyboardEvent) => {
      if (e.key === "Enter") {
        handler();
      }
    };

    document.addEventListener("keydown", handleEnter);
    return () => document.removeEventListener("keydown", handleEnter);
  }, [handler, isActive]);
}

// =============================================================================
// Click on Enter Hook
// =============================================================================

/**
 * Hook to make an element trigger click on Enter key
 * Useful for non-button interactive elements
 */
export function useClickOnEnter(ref: React.RefObject<HTMLElement>) {
  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Enter") {
        e.preventDefault();
        element.click();
      }
    };

    element.addEventListener("keydown", handleKeyDown);
    return () => element.removeEventListener("keydown", handleKeyDown);
  }, [ref]);
}

// =============================================================================
// Mod Key Hook
// =============================================================================

/**
 * Hook to detect if a modifier key is pressed
 */
export function useModifierKey() {
  const [state, setState] = useState({
    ctrl: false,
    shift: false,
    alt: false,
    meta: false,
  });

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      setState({
        ctrl: e.ctrlKey,
        shift: e.shiftKey,
        alt: e.altKey,
        meta: e.metaKey,
      });
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      setState({
        ctrl: e.ctrlKey,
        shift: e.shiftKey,
        alt: e.altKey,
        meta: e.metaKey,
      });
    };

    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("keyup", handleKeyUp);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("keyup", handleKeyUp);
    };
  }, []);

  return state;
}

// =============================================================================
// Typing Detection Hook
// =============================================================================>

/**
 * Hook to detect when the user is typing
 * Useful for pausing animations or hiding tooltips
 */
export function useIsTyping() {
  const [isTyping, setIsTyping] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    const handleKeyDown = () => {
      setIsTyping(true);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(() => {
        setIsTyping(false);
      }, 500);
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return isTyping;
}

// =============================================================================
// Printable Character Detection
// =============================================================================

/**
 * Hook to detect if a key is a printable character
 */
export function useIsPrintableKey() {
  const [char, setChar] = useState<string | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Check if it's a printable character (single character, no modifier)
      if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
        setChar(e.key);
      }
    };

    const handleKeyUp = () => {
      setChar(null);
    };

    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("keyup", handleKeyUp);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("keyup", handleKeyUp);
    };
  }, []);

  return char;
}

// =============================================================================
// Keyboard Navigation Hint Component
// =============================================================================

interface KeyboardShortcutHintProps {
  shortcut: string[];
  description: string;
  className?: string;
}

export function KeyboardShortcutHint({
  shortcut,
  description,
  className = "",
}: KeyboardShortcutHintProps) {
  return (
    <div className={`flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 ${className}`}>
      <span>{description}</span>
      <div className="flex gap-1">
        {shortcut.map((key, index) => (
          <React.Fragment key={key}>
            {index > 0 && <span>+</span>}
            <kbd className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded border border-slate-300 dark:border-slate-700 font-mono text-[10px]">
              {key}
            </kbd>
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

// =============================================================================
// Common Keyboard Shortcuts
// =============================================================================

export const commonShortcuts = {
  save: { key: "s", ctrlKey: true, description: "Save" },
  undo: { key: "z", ctrlKey: true, description: "Undo" },
  redo: { key: "z", ctrlKey: true, shiftKey: true, description: "Redo" },
  find: { key: "f", ctrlKey: true, description: "Find" },
  selectAll: { key: "a", ctrlKey: true, description: "Select All" },
  copy: { key: "c", ctrlKey: true, description: "Copy" },
  paste: { key: "v", ctrlKey: true, description: "Paste" },
  cut: { key: "x", ctrlKey: true, description: "Cut" },
  refresh: { key: "r", ctrlKey: true, description: "Refresh" },
  logout: { key: "q", shiftKey: true, description: "Logout" },
  help: { key: "?", description: "Help" },
  escape: { key: "Escape", description: "Close/Cancel" },
  enter: { key: "Enter", description: "Confirm/Submit" },
  space: { key: " ", description: "Select/Toggle" },
};
