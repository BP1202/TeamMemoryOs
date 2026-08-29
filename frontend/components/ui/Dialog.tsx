/**
 * Dialog — design system primitive.
 *
 * Built on Radix UI Dialog for accessibility.
 * Features: focus trap, ESC close, aria-modal, aria-labelledby.
 */

import {
  Root,
  Trigger,
  Portal,
  Overlay,
  Content,
  Title,
  Description,
  Close,
} from '@radix-ui/react-dialog';
import { forwardRef, type ComponentPropsWithoutRef, type ElementRef, type HTMLAttributes } from 'react';
import { UtilityIcons } from '@config/icons';
import { cn } from '@utils/cn';

// ─── Re-export primitives ──────────────────────────────────────────────────

export const Dialog         = Root;
export const DialogTrigger  = Trigger;
export const DialogPortal   = Portal;
export const DialogClose    = Close;

// ─── Overlay ──────────────────────────────────────────────────────────────

export const DialogOverlay = forwardRef<
  ElementRef<typeof Overlay>,
  ComponentPropsWithoutRef<typeof Overlay>
>(({ className, ...props }, ref) => (
  <Overlay
    ref={ref}
    className={cn(
      'fixed inset-0 z-modal',
      'bg-[var(--color-surface-overlay)] backdrop-blur-sm',
      'data-[state=open]:animate-fade-in',
      'data-[state=closed]:animate-fade-in [&[data-state=closed]]:opacity-0',
      className,
    )}
    {...props}
  />
));
DialogOverlay.displayName = 'DialogOverlay';

// ─── Content ──────────────────────────────────────────────────────────────

export const DialogContent = forwardRef<
  ElementRef<typeof Content>,
  ComponentPropsWithoutRef<typeof Content>
>(({ className, children, ...props }, ref) => (
  <DialogPortal>
    <DialogOverlay />
    <Content
      ref={ref}
      aria-modal="true"
      className={cn(
        'fixed left-1/2 top-1/2 z-modal',
        '-translate-x-1/2 -translate-y-1/2',
        'w-full max-w-lg',
        'bg-surface-elevated border border-border rounded-xl',
        'shadow-dialog p-6',
        'data-[state=open]:animate-slide-up',
        'focus:outline-none',
        className,
      )}
      {...props}
    >
      {children}
      <Close
        className={cn(
          'absolute right-4 top-4',
          'rounded-md p-1',
          'text-text-muted hover:text-text-primary',
          'hover:bg-surface-subtle',
          'transition-colors duration-fast',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
        )}
        aria-label="Close dialog"
      >
        <UtilityIcons.Close className="h-4 w-4" aria-hidden="true" />
      </Close>
    </Content>
  </DialogPortal>
));
DialogContent.displayName = 'DialogContent';

// ─── Title ─────────────────────────────────────────────────────────────────

export const DialogTitle = forwardRef<
  ElementRef<typeof Title>,
  ComponentPropsWithoutRef<typeof Title>
>(({ className, ...props }, ref) => (
  <Title
    ref={ref}
    className={cn('text-lg font-semibold text-text-primary mb-1', className)}
    {...props}
  />
));
DialogTitle.displayName = 'DialogTitle';

// ─── Description ──────────────────────────────────────────────────────────

export const DialogDescription = forwardRef<
  ElementRef<typeof Description>,
  ComponentPropsWithoutRef<typeof Description>
>(({ className, ...props }, ref) => (
  <Description
    ref={ref}
    className={cn('text-sm text-text-secondary mb-4', className)}
    {...props}
  />
));
DialogDescription.displayName = 'DialogDescription';

// ─── Footer ───────────────────────────────────────────────────────────────

export function DialogFooter({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('flex items-center justify-end gap-3 mt-6', className)}
      {...props}
    />
  );
}
DialogFooter.displayName = 'DialogFooter';
