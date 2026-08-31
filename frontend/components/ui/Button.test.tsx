/**
 * Button — component tests.
 * Tests: renders, loading state, disabled state, variants, accessibility.
 */

import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent } from '@testing-library/react';
import { render } from '../../tests/utils/renderWithProviders';
import { Button } from './Button';

describe('Button', () => {
  // ── Renders ───────────────────────────────────────────────────────────

  it('renders children text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('renders with aria-label for icon-only usage', () => {
    render(<Button aria-label="Close dialog" size="icon">×</Button>);
    expect(screen.getByRole('button', { name: /close dialog/i })).toBeInTheDocument();
  });

  // ── Loading state ─────────────────────────────────────────────────────

  it('shows spinner and disables interaction when isLoading', () => {
    const onClick = vi.fn();
    render(<Button isLoading onClick={onClick}>Save</Button>);
    const btn = screen.getByRole('button');
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute('aria-busy', 'true');
    fireEvent.click(btn);
    expect(onClick).not.toHaveBeenCalled();
  });

  // ── Disabled state ────────────────────────────────────────────────────

  it('is not clickable when disabled', () => {
    const onClick = vi.fn();
    render(<Button disabled onClick={onClick}>Delete</Button>);
    const btn = screen.getByRole('button');
    expect(btn).toBeDisabled();
    fireEvent.click(btn);
    expect(onClick).not.toHaveBeenCalled();
  });

  // ── Variants ──────────────────────────────────────────────────────────

  it('applies primary variant classes by default', () => {
    render(<Button>Primary</Button>);
    const btn = screen.getByRole('button');
    // Checks that CVA variant classes are applied (contains bg- token class)
    expect(btn.className).toContain('bg-[var(--btn-primary-bg)]');
  });

  it('applies destructive variant classes', () => {
    render(<Button variant="destructive">Delete</Button>);
    const btn = screen.getByRole('button');
    expect(btn.className).toContain('bg-[var(--btn-destructive-bg)]');
  });

  // ── Accessibility ─────────────────────────────────────────────────────

  it('has correct aria-disabled when disabled', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button')).toHaveAttribute('aria-disabled', 'true');
  });
});
