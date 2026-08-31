/**
 * CommandPalette — component tests.
 * Tests: not shown by default, opens on Ctrl+K, closes on ESC.
 */

import { describe, it, expect } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { render } from '../tests/utils/renderWithProviders';
import { CommandPalette } from './CommandPalette';

describe('CommandPalette', () => {
  it('is not visible on initial render', () => {
    render(<CommandPalette />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('opens on Ctrl+K', async () => {
    render(<CommandPalette />);
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true });

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
  });

  it('opens on Cmd+K (Mac)', async () => {
    render(<CommandPalette />);
    fireEvent.keyDown(window, { key: 'k', metaKey: true });

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
  });

  it('dialog has accessible title', async () => {
    render(<CommandPalette />);
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true });

    await waitFor(() => {
      // DialogTitle is in .sr-only but still accessible
      expect(screen.getByText('Command palette')).toBeInTheDocument();
    });
  });

  it('closes on Ctrl+K toggle', async () => {
    render(<CommandPalette />);

    // Open
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
    await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument());

    // Close via second Ctrl+K
    fireEvent.keyDown(window, { key: 'k', ctrlKey: true });
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  });
});
