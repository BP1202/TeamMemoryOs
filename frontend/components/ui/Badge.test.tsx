/**
 * Badge — component tests.
 */

import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { render } from '../../tests/utils/renderWithProviders';
import { Badge } from './Badge';

describe('Badge', () => {
  it('renders children text', () => {
    render(<Badge>Active</Badge>);
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('applies success variant classes', () => {
    render(<Badge variant="success">Healthy</Badge>);
    expect(screen.getByText('Healthy').className).toContain('bg-[var(--badge-success-bg)]');
  });

  it('applies danger variant classes', () => {
    render(<Badge variant="danger">Failed</Badge>);
    expect(screen.getByText('Failed').className).toContain('bg-[var(--badge-danger-bg)]');
  });
});
