/**
 * Badge — design system primitive.
 *
 * Variants: default | success | warning | danger | info
 *
 * Rules:
 *   - Never reads from store or service.
 *   - Status never communicated by color alone — always includes text.
 */

import { forwardRef, type HTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@utils/cn';

// ─── Variants ─────────────────────────────────────────────────────────────

const badgeVariants = cva(
  [
    'inline-flex items-center gap-1 px-2 py-0.5',
    'text-xs font-medium rounded-full',
    'transition-colors duration-medium',
  ],
  {
    variants: {
      variant: {
        default:     'bg-[var(--badge-default-bg)] text-[var(--badge-default-text)] border border-[var(--badge-default-border)]',
        success:     'bg-[var(--badge-success-bg)] text-[var(--badge-success-text)]',
        warning:     'bg-[var(--badge-warning-bg)] text-[var(--badge-warning-text)]',
        danger:      'bg-[var(--badge-danger-bg)] text-[var(--badge-danger-text)]',
        info:        'bg-[var(--badge-info-bg)] text-[var(--badge-info-text)]',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
);

// ─── Props ─────────────────────────────────────────────────────────────────

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

// ─── Component ─────────────────────────────────────────────────────────────

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, ...props }, ref) => (
    <span
      ref={ref}
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  ),
);

Badge.displayName = 'Badge';
