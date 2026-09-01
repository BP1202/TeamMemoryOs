/**
 * Input — component tests.
 * Tests: renders label, error state, hint, disabled state, accessibility.
 */

import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { render } from '../../tests/utils/renderWithProviders';
import { Input } from './Input';

describe('Input', () => {
  it('renders with label linked by htmlFor', () => {
    render(<Input id="email" label="Email address" />);
    const label = screen.getByText('Email address');
    const input = screen.getByRole('textbox');
    expect(label).toBeInTheDocument();
    expect(input).toHaveAttribute('id', 'email');
    expect(label.closest('label')).toHaveAttribute('for', 'email');
  });

  it('renders error message with role=alert', () => {
    render(<Input id="email" label="Email" error="Email is required" />);
    const errorEl = screen.getByRole('alert');
    expect(errorEl).toHaveTextContent('Email is required');
  });

  it('links error to input via aria-describedby', () => {
    render(<Input id="email" label="Email" error="Email is required" />);
    const input = screen.getByRole('textbox');
    const errorId = `email-error`;
    expect(input).toHaveAttribute('aria-describedby', expect.stringContaining(errorId));
  });

  it('marks input aria-invalid when error present', () => {
    render(<Input id="pw" label="Password" error="Too short" />);
    expect(screen.getByLabelText('Password')).toHaveAttribute('aria-invalid', 'true');
  });

  it('renders hint text when no error', () => {
    render(<Input id="search" label="Search" hint="Use keywords to narrow results" />);
    expect(screen.getByText('Use keywords to narrow results')).toBeInTheDocument();
  });

  it('applies disabled styles when disabled', () => {
    render(<Input id="name" label="Name" disabled />);
    expect(screen.getByRole('textbox')).toBeDisabled();
  });
});
