/**
 * EmptyState — component tests.
 */

import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent } from '@testing-library/react';
import { render } from '../../tests/utils/renderWithProviders';
import { EmptyState } from './EmptyState';
import { Button } from '../ui/Button';

describe('EmptyState', () => {
  it('renders heading', () => {
    render(<EmptyState heading="No memories found" />);
    expect(screen.getByText('No memories found')).toBeInTheDocument();
  });

  it('renders description when provided', () => {
    render(
      <EmptyState
        heading="No memories found"
        description="Create a memory to get started"
      />,
    );
    expect(screen.getByText('Create a memory to get started')).toBeInTheDocument();
  });

  it('renders action CTA', () => {
    const onClick = vi.fn();
    render(
      <EmptyState
        heading="No results"
        action={<Button onClick={onClick}>Add memory</Button>}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: /add memory/i }));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('has role=status for accessibility', () => {
    render(<EmptyState heading="Empty" />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
