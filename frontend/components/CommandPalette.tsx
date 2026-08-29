/**
 * CommandPalette — global Ctrl+K quick-action launcher.
 *
 * Sprint 8.1: Placeholder — registers the keyboard shortcut and renders
 * an accessible dialog shell. Search logic is Sprint 8.4 scope.
 *
 * Accessibility:
 *   - Ctrl+K (or Cmd+K on Mac) opens the dialog.
 *   - ESC closes the dialog (Radix Dialog built-in).
 *   - Focus is trapped inside when open.
 *   - Announces "Command palette" to screen readers.
 */

import { useEffect, useState } from 'react';
import { useReducedMotion } from 'framer-motion';
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from '@components/ui/Dialog';
import { UtilityIcons } from '@config/icons';
import { cn } from '@utils/cn';

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const prefersReduced  = useReducedMotion();

  // ─── Keyboard shortcut ──────────────────────────────────────────────────
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent
        className={cn(
          'max-w-xl p-0 overflow-hidden',
          !prefersReduced && 'transition-all',
        )}
        aria-describedby={undefined}
      >
        <div className="sr-only">
          <DialogTitle>Command palette</DialogTitle>
        </div>

        {/* Search input (placeholder — wired in Sprint 8.4) */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <UtilityIcons.Search
            className="h-4 w-4 text-text-muted flex-shrink-0"
            aria-hidden="true"
          />
          <input
            type="text"
            placeholder="Search memories, entities, run commands…"
            className={cn(
              'flex-1 bg-transparent text-sm text-text-primary',
              'placeholder:text-text-muted outline-none',
            )}
            aria-label="Search"
            autoFocus
            readOnly
          />
          <kbd className="hidden sm:inline-flex items-center gap-0.5 text-xs text-text-muted border border-border rounded px-1.5 py-0.5">
            ESC
          </kbd>
        </div>

        {/* Placeholder body */}
        <div className="px-4 py-8 text-center">
          <p className="text-sm text-text-muted">
            Command search coming in Sprint 8.4
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
