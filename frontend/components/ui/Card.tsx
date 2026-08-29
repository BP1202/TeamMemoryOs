/**
 * Card — design system primitive.
 *
 * Variants: default | elevated | outline
 *
 * Rules:
 *   - Never reads from store or service.
 *   - Used as a layout container — all data passed as children.
 */

import { forwardRef, type HTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@utils/cn';

// ─── Variants ─────────────────────────────────────────────────────────────

const cardVariants = cva(
  'rounded-lg transition-colors duration-medium',
  {
    variants: {
      variant: {
        default: [
          'bg-[var(--card-default-bg)]',
          'border border-[var(--card-default-border)]',
          'shadow-card',
          'p-[var(--card-default-padding)]',
        ],
        elevated: [
          'bg-[var(--card-elevated-bg)]',
          'border border-[var(--card-elevated-border)]',
          'shadow-md',
          'p-[var(--card-elevated-padding)]',
        ],
        outline: [
          'bg-[var(--card-outline-bg)]',
          'border border-[var(--card-outline-border)]',
          'p-[var(--card-outline-padding)]',
          'hover:bg-[var(--card-outline-bg-hover)]',
          'hover:border-[var(--card-outline-border-hover)]',
        ],
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
);

// ─── Props ─────────────────────────────────────────────────────────────────

export interface CardProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

// ─── Component ─────────────────────────────────────────────────────────────

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardVariants({ variant }), className)}
      {...props}
    />
  ),
);

Card.displayName = 'Card';

// ─── Sub-components ────────────────────────────────────────────────────────

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex items-start gap-3 mb-4', className)} {...props} />
  ),
);
CardHeader.displayName = 'CardHeader';

export const CardTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn('text-base font-semibold text-text-primary leading-tight', className)}
      {...props}
    />
  ),
);
CardTitle.displayName = 'CardTitle';

export const CardDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-text-secondary', className)}
      {...props}
    />
  ),
);
CardDescription.displayName = 'CardDescription';

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('', className)} {...props} />
  ),
);
CardContent.displayName = 'CardContent';

export const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center gap-3 mt-4 pt-4 border-t border-border', className)}
      {...props}
    />
  ),
);
CardFooter.displayName = 'CardFooter';
