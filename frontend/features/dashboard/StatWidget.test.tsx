/**
 * StatWidget — component tests.
 * Tests: loading state, data state, error state.
 */

import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { render } from '../../tests/utils/renderWithProviders';
import { StatWidget } from './StatWidget';
import { NavIcons } from '@config/icons';

describe('StatWidget', () => {
  it('renders label', () => {
    render(<StatWidget label="Memories" value={42} icon={NavIcons.Memory} />);
    expect(screen.getByText('Memories')).toBeInTheDocument();
  });

  it('renders value when data is present', () => {
    render(<StatWidget label="Memories" value={42} icon={NavIcons.Memory} />);
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('renders loading skeleton when isLoading=true', () => {
    render(<StatWidget label="Memories" icon={NavIcons.Memory} isLoading />);
    // The skeleton has aria-hidden — check the container has aria-busy
    expect(screen.getByRole('status')).toHaveAttribute('aria-busy', 'true');
  });

  it('renders error text when isError=true', () => {
    render(<StatWidget label="Memories" icon={NavIcons.Memory} isError />);
    expect(screen.getByText(/unavailable/i)).toBeInTheDocument();
  });

  it('has role=status for accessibility', () => {
    render(<StatWidget label="Agents" value={2} icon={NavIcons.Agents} />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
