/**
 * Button — design system primitive.
 *
 * Variants: primary | secondary | ghost | destructive
 * Sizes:    sm | md | lg | icon
 *
 * Rules:
 *   - Never reads from any store or service.
 *   - Never calls API directly.
 *   - Supports loading, disabled, and all accessible states.
 */

import { forwardRef, type ButtonHTMLAttributes } from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@utils/cn';
import { UtilityIcons } from '@config/icons';

// ─── Variants ─────────────────────────────────────────────────────────────

const buttonVariants = cva(
  // Base styles
  [
    'inline-flex items-center justify-center gap-2',
    'font-medium rounded-md',
    'transition-colors duration-medium ease-in-out',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
    'focus-visible:ring-offset-surface-base',
    'disabled:pointer-events-none disabled:cursor-not-allowed',
    'select-none',
  ],
  {
    variants: {
      variant: {
        primary: [
          'bg-[var(--btn-primary-bg)] text-[var(--btn-primary-text)]',
          'hover:bg-[var(--btn-primary-bg-hover)]',
          'active:bg-[var(--btn-primary-bg-active)]',
          'disabled:bg-[var(--btn-primary-bg-disabled)] disabled:text-[var(--btn-primary-text-disabled)]',
          'shadow-glow',
          'focus-visible:ring-[var(--btn-primary-ring)]',
        ],
        secondary: [
          'bg-[var(--btn-secondary-bg)] text-[var(--btn-secondary-text)]',
          'border border-[var(--btn-secondary-border)]',
          'hover:bg-[var(--btn-secondary-bg-hover)] hover:border-[var(--btn-secondary-border-hover)]',
          'disabled:bg-[var(--btn-secondary-bg-disabled)] disabled:text-[var(--btn-secondary-text-disabled)]',
          'focus-visible:ring-[var(--btn-secondary-ring)]',
        ],
        ghost: [
          'bg-[var(--btn-ghost-bg)] text-[var(--btn-ghost-text)]',
          'hover:bg-[var(--btn-ghost-bg-hover)] hover:text-[var(--btn-ghost-text-hover)]',
          'disabled:text-[var(--btn-ghost-text-disabled)]',
          'focus-visible:ring-[var(--btn-ghost-ring)]',
        ],
        destructive: [
          'bg-[var(--btn-destructive-bg)] text-[var(--btn-destructive-text)]',
          'hover:bg-[var(--btn-destructive-bg-hover)]',
          'active:bg-[var(--btn-destructive-bg-active)]',
          'disabled:bg-[var(--btn-destructive-bg-disabled)] disabled:text-[var(--btn-destructive-text-disabled)]',
          'shadow-danger',
          'focus-visible:ring-[var(--btn-destructive-ring)]',
        ],
      },
      size: {
        sm:   'h-8  px-3 text-xs',
        md:   'h-9  px-4 text-sm',
        lg:   'h-11 px-6 text-base',
        icon: 'h-9  w-9  p-0',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  },
);

// ─── Props ─────────────────────────────────────────────────────────────────

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** Render as a child element (Radix Slot). */
  asChild?: boolean;
  /** Show spinner and block interaction. */
  isLoading?: boolean;
  /** Accessible label for icon-only buttons. Required when no text children. */
  'aria-label'?: string;
}

// ─── Component ─────────────────────────────────────────────────────────────

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      asChild = false,
      isLoading = false,
      disabled,
      children,
      ...props
    },
    ref,
  ) => {
    const Comp = asChild ? Slot : 'button';

    return (
      <Comp
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        disabled={disabled || isLoading}
        aria-disabled={disabled || isLoading}
        aria-busy={isLoading}
        {...props}
      >
        {isLoading && (
          <UtilityIcons.Loading
            className="h-4 w-4 animate-spin"
            aria-hidden="true"
          />
        )}
        {children}
      </Comp>
    );
  },
);

Button.displayName = 'Button';
