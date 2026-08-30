/**
 * Tooltip — design system primitive.
 * Built on Radix UI Tooltip for accessibility.
 *
 * Rules:
 *   - Never reads from store or service.
 *   - Always pair with a meaningful content string.
 */

import {
  Provider,
  Root,
  Trigger,
  Content,
  Portal,
} from '@radix-ui/react-tooltip';
import { forwardRef, type ComponentPropsWithoutRef, type ElementRef } from 'react';
import { cn } from '@utils/cn';

// ─── Provider (mount once at app root or layout level) ────────────────────

export const TooltipProvider = Provider;

// ─── Primitives ────────────────────────────────────────────────────────────

export const Tooltip        = Root;
export const TooltipTrigger = Trigger;
export const TooltipPortal  = Portal;

// ─── Content ──────────────────────────────────────────────────────────────

export const TooltipContent = forwardRef<
  ElementRef<typeof Content>,
  ComponentPropsWithoutRef<typeof Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
  <Portal>
    <Content
      ref={ref}
      sideOffset={sideOffset}
      className={cn(
        'z-tooltip rounded-md px-2.5 py-1.5',
        'bg-surface-elevated border border-border',
        'text-xs text-text-primary shadow-card',
        'animate-fade-in',
        className,
      )}
      {...props}
    />
  </Portal>
));
TooltipContent.displayName = 'TooltipContent';
