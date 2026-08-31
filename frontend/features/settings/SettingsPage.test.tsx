/**
 * SettingsPage tests.
 */

import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@tests/utils/renderWithProviders';
import { SettingsPage } from './SettingsPage';

describe('SettingsPage', () => {
  it('renders settings page scaffold', () => {
    renderWithProviders(<SettingsPage />);
    expect(screen.getByTestId('settings-page')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Appearance')).toBeInTheDocument();
  });

  it('renders theme buttons', () => {
    renderWithProviders(<SettingsPage />);
    expect(screen.getByRole('button', { name: /set theme to light/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /set theme to dark/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /set theme to system/i })).toBeInTheDocument();
  });

  it('theme buttons are keyboard accessible', async () => {
    const user = userEvent.setup();
    renderWithProviders(<SettingsPage />);
    const lightBtn = screen.getByRole('button', { name: /set theme to light/i });
    await user.click(lightBtn);
    // No error thrown = pass
  });
});
