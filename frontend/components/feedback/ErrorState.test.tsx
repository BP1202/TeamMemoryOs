/**
 * ErrorState — component tests.
 */

import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent } from '@testing-library/react';
import { render } from '../../tests/utils/renderWithProviders';
import { ErrorState } from './ErrorState';

describe('ErrorState', () => {
  it('renders default heading', () => {
    render(<ErrorState />);
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });

  it('renders custom heading and message', () => {
    render(<ErrorState heading="Load failed" message="Could not fetch memories" />);
    expect(screen.getByText('Load failed')).toBeInTheDocument();
    expect(screen.getByText('Could not fetch memories')).toBeInTheDocument();
  });

  it('calls onRetry when retry button clicked', () => {
    const onRetry = vi.fn();
    render(<ErrorState onRetry={onRetry} />);
    fireEvent.click(screen.getByRole('button', { name: /try again/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('has role=alert for immediate screen reader announcement', () => {
    render(<ErrorState />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('does not render retry button when onRetry not provided', () => {
    render(<ErrorState />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
