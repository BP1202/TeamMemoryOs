/**
 * GraphPage test suite — Sprint 8.3
 *
 * Covers:
 *   - Graph renders entity names in fallback table (data state)
 *   - Loading state (spinner)
 *   - Empty state
 *   - Error state with retry
 *   - Node / table row selection opens inspector drawer
 *   - Drawer content shows entity details
 *   - Drawer close on ESC
 *   - Expand neighbors button
 *   - Search filters fallback table
 *   - Entity type filter
 *   - Reset graph
 *
 * React Flow canvas is not rendered in jsdom — we test through the
 * accessible fallback table and the inspector drawer.
 *
 * Stack: Vitest + RTL + MSW
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '../../tests/mocks/server';
import { mockEntities } from '../../tests/mocks/handlers';
import { render } from '../../tests/utils/renderWithProviders';
import { GraphPage } from './GraphPage';
import { useGraphStore } from '@stores/graphStore';
import { useAuthStore } from '@stores/authStore';

const BASE = 'http://localhost:8000';

// ─── Mock React Flow (not supported in jsdom) ──────────────────────────────
// We render the fallback table and inspector in tests. React Flow itself
// is tested at the integration level only.

vi.mock('@xyflow/react', async () => {
  const actual = await vi.importActual<typeof import('@xyflow/react')>('@xyflow/react');
  return {
    ...actual,
    ReactFlow: ({ children }: { children?: React.ReactNode }) => (
      <div data-testid="react-flow-mock">{children}</div>
    ),
    ReactFlowProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
    Background: () => null,
    Controls:   () => null,
    MiniMap:    () => null,
    Handle:     () => null,
    MarkerType: actual.MarkerType,
    getBezierPath: () => ['', 0, 0] as [string, number, number],
    BaseEdge:   () => null,
    EdgeLabelRenderer: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  };
});

// ─── Helpers ───────────────────────────────────────────────────────────────

function seedAuth() {
  useAuthStore.setState({
    token: 'mock-token',
    user: {
      id: 'usr-01',
      email: 'test@example.com',
      full_name: 'Test User',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    isAuthenticated: true,
  });
}

beforeEach(() => {
  seedAuth();
  useGraphStore.setState({
    selectedEntityId:  null,
    isInspectorOpen:   false,
    expandedEntityIds: [],
    filters: { entityType: 'all', relationshipType: 'all', search: '' },
  });
});

// ─── 1. Data state ─────────────────────────────────────────────────────────

describe('GraphPage — data state', () => {
  it('renders entity names in fallback table after load', async () => {
    render(<GraphPage />);
    await waitFor(() => {
      expect(screen.getByText('AuthService')).toBeInTheDocument();
    });
    expect(screen.getByText('PostgreSQL')).toBeInTheDocument();
    expect(screen.getByText('Alice Engineer')).toBeInTheDocument();
  });

  it('shows entity count in fallback table heading', async () => {
    render(<GraphPage />);
    await waitFor(() => {
      expect(screen.getByText(/3 entities/)).toBeInTheDocument();
    });
  });
});

// ─── 2. Loading state ──────────────────────────────────────────────────────

describe('GraphPage — loading state', () => {
  it('shows spinner while fetching', () => {
    server.use(
      http.get(`${BASE}/api/v1/entities/organization/:orgId`, async () => {
        await new Promise((r) => setTimeout(r, 500));
        return HttpResponse.json(mockEntities, { status: 200 });
      }),
    );
    render(<GraphPage />);
    expect(screen.getByTestId('graph-loading')).toBeInTheDocument();
  });
});

// ─── 3. Empty state ────────────────────────────────────────────────────────

describe('GraphPage — empty state', () => {
  it('shows empty state when no entities exist', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entities/organization/:orgId`, () => {
        return HttpResponse.json([], { status: 200 });
      }),
    );
    render(<GraphPage />);
    await waitFor(() => {
      expect(screen.getByText('No entities yet')).toBeInTheDocument();
    });
  });
});

// ─── 4. Error state ────────────────────────────────────────────────────────

describe('GraphPage — error state', () => {
  it('shows error state when API fails', async () => {
    server.use(
      http.get(`${BASE}/api/v1/entities/organization/:orgId`, () => {
        return HttpResponse.json({ detail: 'Internal error' }, { status: 500 });
      }),
    );
    render(<GraphPage />);
    await waitFor(() => {
      expect(screen.getByText('Failed to load graph')).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('retries on error button click', async () => {
    let callCount = 0;
    server.use(
      http.get(`${BASE}/api/v1/entities/organization/:orgId`, () => {
        callCount++;
        if (callCount === 1) return HttpResponse.json({ detail: 'error' }, { status: 500 });
        return HttpResponse.json(mockEntities, { status: 200 });
      }),
    );
    render(<GraphPage />);
    await waitFor(() => {
      expect(screen.getByText('Failed to load graph')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByRole('button', { name: /try again/i }));
    await waitFor(() => {
      expect(screen.getByText('AuthService')).toBeInTheDocument();
    });
  });
});

// ─── 5. Node / table row selection ────────────────────────────────────────

describe('GraphPage — entity selection', () => {
  it('opens inspector drawer when fallback table row is clicked', async () => {
    render(<GraphPage />);
    await waitFor(() => {
      expect(screen.getByText('AuthService')).toBeInTheDocument();
    });

    // Click the AuthService row in fallback table
    const rows = screen.getAllByRole('row');
    const authRow = rows.find((r) => r.textContent?.includes('AuthService'));
    expect(authRow).toBeTruthy();
    await userEvent.click(authRow!);

    await waitFor(() => {
      expect(useGraphStore.getState().selectedEntityId).toBe('ent-01');
      expect(useGraphStore.getState().isInspectorOpen).toBe(true);
    });
  });
});

// ─── 6. Inspector drawer ───────────────────────────────────────────────────

describe('GraphPage — inspector drawer', () => {
  it('shows entity detail when drawer is open', async () => {
    useGraphStore.setState((s) => ({
      ...s,
      selectedEntityId: 'ent-01',
      isInspectorOpen:  true,
    }));

    render(<GraphPage />);
    await waitFor(() => {
      // Inspector shows entity name
      const headings = screen.getAllByText('AuthService');
      expect(headings.length).toBeGreaterThanOrEqual(1);
    });
    // Description appears in both the fallback table td and the drawer body — use getAllByText
    await waitFor(() => {
      const els = screen.getAllByText('Handles authentication and JWT issuance.');
      expect(els.length).toBeGreaterThanOrEqual(1);
      // At least one should be a <p> (drawer body)
      const paraEl = els.find((el) => el.tagName.toLowerCase() === 'p');
      expect(paraEl).toBeTruthy();
    });
  });

  it('closes drawer on ESC', async () => {
    useGraphStore.setState((s) => ({
      ...s,
      selectedEntityId: 'ent-01',
      isInspectorOpen:  true,
    }));
    render(<GraphPage />);
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
    await userEvent.keyboard('{Escape}');
    await waitFor(() => {
      expect(useGraphStore.getState().isInspectorOpen).toBe(false);
    });
  });

  it('shows expand neighbors button in drawer', async () => {
    useGraphStore.setState((s) => ({
      ...s,
      selectedEntityId: 'ent-01',
      isInspectorOpen:  true,
    }));
    render(<GraphPage />);
    await waitFor(() => {
      expect(screen.getByTestId('expand-neighbors-btn')).toBeInTheDocument();
    });
  });

  it('expand neighbors button marks entity as expanded', async () => {
    useGraphStore.setState((s) => ({
      ...s,
      selectedEntityId: 'ent-01',
      isInspectorOpen:  true,
    }));
    render(<GraphPage />);
    await waitFor(() => {
      expect(screen.getByTestId('expand-neighbors-btn')).toBeInTheDocument();
    });
    await userEvent.click(screen.getByTestId('expand-neighbors-btn'));
    await waitFor(() => {
      expect(useGraphStore.getState().expandedEntityIds).toContain('ent-01');
    });
  });
});

// ─── 7. Search filtering ───────────────────────────────────────────────────

describe('GraphPage — search filter', () => {
  it('search input has role="search" wrapper', async () => {
    render(<GraphPage />);
    await waitFor(() => {
      expect(screen.getByRole('search', { name: /search entities/i })).toBeInTheDocument();
    });
  });

  it('filters fallback table entries by search text', async () => {
    render(<GraphPage />);
    await waitFor(() => {
      expect(screen.getByText('AuthService')).toBeInTheDocument();
    });

    // Directly set the search filter
    useGraphStore.setState((s) => ({
      ...s,
      filters: { ...s.filters, search: 'Alice' },
    }));

    await waitFor(() => {
      expect(screen.getByText('Alice Engineer')).toBeInTheDocument();
    });
    // AuthService rows should be gone from fallback table
    // Check by querying rows with role=row in the accessible fallback section
    await waitFor(() => {
      const rows = document.querySelectorAll('table tbody tr');
      const hasAuth = Array.from(rows).some((row) => row.textContent?.includes('AuthService'));
      expect(hasAuth).toBe(false);
    });
  });
});

// ─── 8. Entity type filter ─────────────────────────────────────────────────

describe('GraphPage — entity type filter', () => {
  it('renders entity type filter buttons', async () => {
    render(<GraphPage />);
    await waitFor(() => {
      expect(screen.getByText('AuthService')).toBeInTheDocument();
    });
    // Check for filter group
    expect(screen.getByRole('group', { name: /filter by entity type/i })).toBeInTheDocument();
  });

  it('filters to single type when chip is pressed', async () => {
    render(<GraphPage />);
    await waitFor(() => {
      expect(screen.getByText('AuthService')).toBeInTheDocument();
    });

    // Apply SERVICE filter via store
    useGraphStore.setState((s) => ({
      ...s,
      filters: { ...s.filters, entityType: 'SERVICE' },
    }));

    await waitFor(() => {
      expect(screen.getByText('AuthService')).toBeInTheDocument();
    });
    // PostgreSQL rows (TECHNOLOGY) should be gone from fallback table
    await waitFor(() => {
      const rows = document.querySelectorAll('table tbody tr');
      const hasPostgres = Array.from(rows).some((row) => row.textContent?.includes('PostgreSQL'));
      expect(hasPostgres).toBe(false);
    });
  });
});

// ─── 9. Reset graph ────────────────────────────────────────────────────────

describe('GraphPage — reset', () => {
  it('reset button clears filters and selection', async () => {
    // Start with NO drawer open so Radix doesn't intercept pointer events
    useGraphStore.setState((s) => ({
      ...s,
      selectedEntityId:  null,
      isInspectorOpen:   false,
      expandedEntityIds: ['ent-01'],
      filters: { entityType: 'SERVICE', relationshipType: 'DEPENDS_ON', search: 'auth' },
    }));

    render(<GraphPage />);
    await waitFor(() => {
      expect(screen.getByTestId('reset-graph-btn')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByTestId('reset-graph-btn'));

    await waitFor(() => {
      const state = useGraphStore.getState();
      expect(state.selectedEntityId).toBeNull();
      expect(state.expandedEntityIds).toHaveLength(0);
      expect(state.filters.entityType).toBe('all');
      expect(state.filters.search).toBe('');
    });
  });
});
