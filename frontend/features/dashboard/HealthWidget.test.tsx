/**
 * HealthWidget — component tests.
 * Tests: loading state, healthy state, error state.
 */

import { describe, it, expect } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '../../tests/mocks/server';
import { render } from '../../tests/utils/renderWithProviders';
import { HealthWidget } from './HealthWidget';

describe('HealthWidget', () => {
  it('renders loading skeletons initially', () => {
    render(<HealthWidget />);
    // aria-busy should be true during loading
    expect(screen.getByRole('status', { name: /system health/i })).toHaveAttribute('aria-busy', 'true');
  });

  it('renders healthy status badges for backend and db', async () => {
    render(<HealthWidget />);

    await waitFor(() => {
      // Both backend AND database return 'healthy' — use getAllByText
      const healthyBadges = screen.getAllByText('healthy');
      expect(healthyBadges).toHaveLength(2);
    });

    // Both row labels should be present
    expect(screen.getByText('Backend')).toBeInTheDocument();
    expect(screen.getByText('Database')).toBeInTheDocument();
  });

  it('renders error status when backend is down', async () => {
    server.use(
      http.get('http://localhost:8000/api/v1/health/', () =>
        HttpResponse.json({ detail: 'Service unavailable' }, { status: 503 }),
      ),
    );

    render(<HealthWidget />);

    await waitFor(
      () => {
        // error badge appears for backend after query fails
        const errorBadges = screen.getAllByText('error');
        expect(errorBadges.length).toBeGreaterThan(0);
      },
      { timeout: 3000 },
    );
  });
});
