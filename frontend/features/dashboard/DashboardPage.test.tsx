/**
 * DashboardPage — integration tests.
 * Tests: renders, stats loading, stats data.
 */

import { describe, it, expect } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { render } from '../../tests/utils/renderWithProviders';
import { DashboardPage } from './DashboardPage';

describe('DashboardPage', () => {
  it('renders the dashboard page container', () => {
    render(<DashboardPage />);
    expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
  });

  it('renders the Overview section heading', () => {
    render(<DashboardPage />);
    expect(screen.getByText(/overview/i)).toBeInTheDocument();
  });

  it('renders the three stat widgets in loading state initially', () => {
    render(<DashboardPage />);
    const statWidgets = screen.getAllByRole('status', { name: /count/i });
    // Memory, Scenarios, Agents
    expect(statWidgets).toHaveLength(3);
  });

  it('renders stats once data loads', async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      // mock returns 3 memories, 1 scenario, 2 agents
      expect(screen.getByText('3')).toBeInTheDocument(); // memory count
      expect(screen.getByText('1')).toBeInTheDocument(); // scenario count
      expect(screen.getByText('2')).toBeInTheDocument(); // agent count
    });
  });

  it('renders the health widget', () => {
    render(<DashboardPage />);
    expect(screen.getByRole('status', { name: /system health/i })).toBeInTheDocument();
  });

  it('renders workspace quick actions', () => {
    render(<DashboardPage />);
    expect(screen.getByRole('list', { name: /quick actions/i })).toBeInTheDocument();
  });
});
