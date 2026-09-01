/**
 * Spinner — component tests.
 */

import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { render } from '../../tests/utils/renderWithProviders';
import { Spinner } from './Spinner';

describe('Spinner', () => {
  it('renders with default label', () => {
    render(<Spinner />);
    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument();
  });

  it('renders with custom label', () => {
    render(<Spinner label="Saving changes…" />);
    expect(screen.getByRole('status', { name: /saving changes/i })).toBeInTheDocument();
  });
});
