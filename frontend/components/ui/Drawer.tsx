/**
 * Drawer — design system primitive.
 * Slide-in panel from the right side of the viewport.
 *
 * Built on Radix UI Dialog for accessibility:
 *   focus trap, ESC close, aria-modal, aria-labelledby, portal.
 *
 * Rules:
 *   - Never reads from store or service.
 *   - Used as a layout wrapper — all data passed as children.
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

export const Drawer        = Root;
export const DrawerTrigger = Trigger;
export const DrawerPortal  = Portal;
export const DrawerClose   = Close;

// ─── Overlay ──────────────────────────────────────────────────────────────

export const DrawerOverlay = forwardRef<
  ElementRef<typeof Overlay>,
  ComponentPropsWithoutRef<typeof Overlay>
>(({ className, ...props }, ref) => (
  <Overlay
    ref={ref}
    className={cn(
      'fixed inset-0 z-modal',
      'bg-[var(--color-surface-overlay)] backdrop-blur-sm',
      'data-[state=open]:animate-fade-in',
      className,
    )}
    {...props}
  />
));
DrawerOverlay.displayName = 'DrawerOverlay';

// ─── Content ──────────────────────────────────────────────────────────────

export const DrawerContent = forwardRef<
  ElementRef<typeof Content>,
  ComponentPropsWithoutRef<typeof Content> & { size?: 'sm' | 'md' | 'lg' }
>(({ className, children, size = 'md', ...props }, ref) => {
  const widthClass = {
    sm: 'w-full max-w-sm',
    md: 'w-full max-w-lg',
    lg: 'w-full max-w-2xl',
  }[size];

  return (
    <DrawerPortal>
      <DrawerOverlay />
      <Content
        ref={ref}
        aria-modal="true"
        className={cn(
          'fixed right-0 top-0 bottom-0 z-modal',
          widthClass,
          'bg-surface-elevated border-l border-border',
          'shadow-dialog',
          'flex flex-col overflow-hidden',
          'focus:outline-none',
          // Slide in from right
          'data-[state=open]:animate-slide-in-right',
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
          aria-label="Close panel"
        >
          <UtilityIcons.Close className="h-4 w-4" aria-hidden="true" />
        </Close>
      </Content>
    </DrawerPortal>
  );
});
DrawerContent.displayName = 'DrawerContent';

// ─── Header ─────────────────────────────────────────────────────────────────

export function DrawerHeader({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'px-6 py-4 border-b border-border flex-shrink-0',
        className,
      )}
      {...props}
    />
  );
}
DrawerHeader.displayName = 'DrawerHeader';

// ─── Title ─────────────────────────────────────────────────────────────────

export const DrawerTitle = forwardRef<
  ElementRef<typeof Title>,
  ComponentPropsWithoutRef<typeof Title>
>(({ className, ...props }, ref) => (
  <Title
    ref={ref}
    className={cn('text-lg font-semibold text-text-primary pr-8', className)}
    {...props}
  />
));
DrawerTitle.displayName = 'DrawerTitle';

// ─── Description ──────────────────────────────────────────────────────────

export const DrawerDescription = forwardRef<
  ElementRef<typeof Description>,
  ComponentPropsWithoutRef<typeof Description>
>(({ className, ...props }, ref) => (
  <Description
    ref={ref}
    className={cn('text-sm text-text-secondary mt-1', className)}
    {...props}
  />
));
DrawerDescription.displayName = 'DrawerDescription';

// ─── Body ──────────────────────────────────────────────────────────────────

export function DrawerBody({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('flex-1 overflow-y-auto px-6 py-4', className)}
      {...props}
    />
  );
}
DrawerBody.displayName = 'DrawerBody';

// ─── Footer ───────────────────────────────────────────────────────────────

export function DrawerFooter({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'px-6 py-4 border-t border-border flex-shrink-0',
        'flex items-center justify-end gap-3',
        className,
      )}
      {...props}
    />
  );
}
DrawerFooter.displayName = 'DrawerFooter';
