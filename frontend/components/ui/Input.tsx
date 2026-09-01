/**
 * Input — design system primitive.
 *
 * States: default | focus | error | disabled
 *
 * Rules:
 *   - Never reads from store or service.
 *   - Label linked via htmlFor/id.
 *   - Error message linked via aria-describedby.
 */

import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '@utils/cn';

// ─── Props ─────────────────────────────────────────────────────────────────

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Input label — renders a <label> linked by id. */
  label?: string;
  /** Error message — renders below input, linked via aria-describedby. */
  error?: string;
  /** Hint text shown below input when no error. */
  hint?: string;
}

// ─── Component ─────────────────────────────────────────────────────────────

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, id, ...props }, ref) => {
    const inputId = id ?? `input-${Math.random().toString(36).slice(2)}`;
    const errorId = `${inputId}-error`;
    const hintId  = `${inputId}-hint`;

    const describedBy = [
      error ? errorId : null,
      hint  ? hintId  : null,
    ]
      .filter(Boolean)
      .join(' ') || undefined;

    return (
      <div className="flex flex-col gap-1.5 w-full">
        {label && (
          <label
            htmlFor={inputId}
            className={cn(
              'text-sm font-medium',
              error ? 'text-[var(--input-error-label)]' : 'text-text-secondary',
            )}
          >
            {label}
          </label>
        )}

        <input
          ref={ref}
          id={inputId}
          aria-describedby={describedBy}
          aria-invalid={error ? 'true' : undefined}
          className={cn(
            'w-full rounded-md text-sm transition-colors duration-medium',
            'bg-[var(--input-bg)] text-[var(--input-text)]',
            'border border-[var(--input-border)]',
            'px-[var(--input-padding-x)] py-[var(--input-padding-y)]',
            'placeholder:text-[var(--input-placeholder)]',
            'focus:outline-none focus:border-[var(--input-focus-border)]',
            'focus:ring-2 focus:ring-[var(--input-focus-ring)]',
            'disabled:bg-[var(--input-disabled-bg)]',
            'disabled:border-[var(--input-disabled-border)]',
            'disabled:text-[var(--input-disabled-text)]',
            'disabled:cursor-not-allowed',
            error && [
              'border-[var(--input-error-border)]',
              'ring-2 ring-[var(--input-error-ring)]',
            ],
            className,
          )}
          {...props}
        />

        {error && (
          <p
            id={errorId}
            role="alert"
            className="text-xs text-[var(--input-error-label)]"
          >
            {error}
          </p>
        )}

        {!error && hint && (
          <p id={hintId} className="text-xs text-text-muted">
            {hint}
          </p>
        )}
      </div>
    );
  },
);

Input.displayName = 'Input';
