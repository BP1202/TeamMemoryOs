/**
 * MemoryPage test suite — Sprint 8.2
 *
 * Covers:
 *   - Memory table renders with data
 *   - Loading state (skeleton)
 *   - Empty state (no data)
 *   - Error state with retry
 *   - Search filters entries
 *   - Memory type filter chip
 *   - Row click opens detail drawer
 *   - Create memory drawer: success + failure
 *   - Scenario creation dialog: success + failure
 *   - Scenario filter chips
 *
 * Stack: Vitest + RTL + MSW
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '../../tests/mocks/server';
import {
  mockMemoryEntries,
  mockMemoryEntry,
} from '../../tests/mocks/handlers';
import { render } from '../../tests/utils/renderWithProviders';
import { MemoryPage } from './MemoryPage';
import { useMemoryStore } from '@stores/memoryStore';
import { useAuthStore } from '@stores/authStore';

const BASE = 'http://localhost:8000';

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
  useMemoryStore.setState({
    isDetailDrawerOpen: false,
    selectedMemoryId: null,
    isCreateDrawerOpen: false,
    filters: { memoryType: 'all', scenarioId: 'all', search: '' },
  });
});

// ─── 1. Table renders with data ────────────────────────────────────────────

describe('MemoryPage — data state', () => {
  it('renders memory entries after loading', async () => {
    render(<MemoryPage />);

    // Loading skeleton first
    expect(screen.getByRole('status', { name: /loading memories/i })).toBeInTheDocument();

    // Data appears
    await waitFor(() => {
      expect(screen.getByText('Adopt pgvector for semantic search')).toBeInTheDocument();
    });

    expect(screen.getByText('Database connection pool exhaustion')).toBeInTheDocument();
    expect(screen.getByText('Team context: backend ownership')).toBeInTheDocument();
  });

  it('renders memory type badges', async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByText('Adopt pgvector for semantic search')).toBeInTheDocument();
    });
    // Decision badge — multiple may exist (filter chip + table badge); verify at least one badge span
    const decisionBadges = screen.getAllByText('Decision');
    expect(decisionBadges.length).toBeGreaterThanOrEqual(1);
    // At least one should be a badge span (not the type filter button)
    const badgeSpan = decisionBadges.find((el) => el.tagName.toLowerCase() === 'span');
    expect(badgeSpan).toBeTruthy();
  });

  it('shows entry count summary', async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByText(/3 entries/i)).toBeInTheDocument();
    });
  });
});

// ─── 2. Loading state ──────────────────────────────────────────────────────

describe('MemoryPage — loading state', () => {
  it('shows skeleton while fetching', () => {
    // Delay the MSW response
    server.use(
      http.get(`${BASE}/api/v1/memory/organization/:orgId`, async () => {
        await new Promise((r) => setTimeout(r, 200));
        return HttpResponse.json(mockMemoryEntries, { status: 200 });
      }),
    );

    render(<MemoryPage />);
    expect(screen.getByRole('status', { name: /loading memories/i })).toBeInTheDocument();
  });
});

// ─── 3. Empty state ────────────────────────────────────────────────────────

describe('MemoryPage — empty state', () => {
  it('shows empty state when no memories exist', async () => {
    server.use(
      http.get(`${BASE}/api/v1/memory/organization/:orgId`, () => {
        return HttpResponse.json([], { status: 200 });
      }),
    );

    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByText('No memories yet')).toBeInTheDocument();
    });
    expect(screen.getByText('Create your first memory')).toBeInTheDocument();
  });

  it('shows filtered empty state when filters match nothing', async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByText('Adopt pgvector for semantic search')).toBeInTheDocument();
    });

    // Apply a type filter that matches nothing in the fake data
    useMemoryStore.setState((s) => ({
      ...s,
      filters: { ...s.filters, memoryType: 'artifact' },
    }));

    await waitFor(() => {
      expect(screen.getByText('No matching memories')).toBeInTheDocument();
    });
  });
});

// ─── 4. Error state ────────────────────────────────────────────────────────

describe('MemoryPage — error state', () => {
  it('shows error state when API fails', async () => {
    server.use(
      http.get(`${BASE}/api/v1/memory/organization/:orgId`, () => {
        return HttpResponse.json({ detail: 'Internal server error' }, { status: 500 });
      }),
    );

    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByText('Failed to load memories')).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('retries on error button click', async () => {
    let callCount = 0;
    server.use(
      http.get(`${BASE}/api/v1/memory/organization/:orgId`, () => {
        callCount++;
        if (callCount === 1) {
          return HttpResponse.json({ detail: 'error' }, { status: 500 });
        }
        return HttpResponse.json(mockMemoryEntries, { status: 200 });
      }),
    );

    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByText('Failed to load memories')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /try again/i }));
    await waitFor(() => {
      expect(screen.getByText('Adopt pgvector for semantic search')).toBeInTheDocument();
    });
  });
});

// ─── 5. Search ─────────────────────────────────────────────────────────────

describe('MemoryPage — search', () => {
  it('filters entries by search text', async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByText('Adopt pgvector for semantic search')).toBeInTheDocument();
    });

    // Directly set the filter (simulates debounced search result)
    useMemoryStore.setState((s) => ({
      ...s,
      filters: { ...s.filters, search: 'pgvector' },
    }));

    await waitFor(() => {
      expect(screen.getByText('Adopt pgvector for semantic search')).toBeInTheDocument();
      expect(screen.queryByText('Database connection pool exhaustion')).not.toBeInTheDocument();
    });
  });

  it('search input has role="search" wrapper', async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByRole('search', { name: /search memories/i })).toBeInTheDocument();
    });
  });
});

// ─── 6. Memory type filter ─────────────────────────────────────────────────

describe('MemoryPage — type filter', () => {
  it('filters by memory type chip', async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByText('Adopt pgvector for semantic search')).toBeInTheDocument();
    });

    // Set insight filter
    useMemoryStore.setState((s) => ({
      ...s,
      filters: { ...s.filters, memoryType: 'insight' },
    }));

    await waitFor(() => {
      expect(screen.getByText('Database connection pool exhaustion')).toBeInTheDocument();
      expect(screen.queryByText('Adopt pgvector for semantic search')).not.toBeInTheDocument();
    });
  });
});

// ─── 7. Detail drawer ──────────────────────────────────────────────────────

describe('MemoryPage — detail drawer', () => {
  it('opens detail drawer on row click', async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByText('Adopt pgvector for semantic search')).toBeInTheDocument();
    });

    const rows = screen.getAllByRole('row');
    // Click first data row (skip header)
    await userEvent.click(rows[1]);

    await waitFor(() => {
      expect(useMemoryStore.getState().isDetailDrawerOpen).toBe(true);
      expect(useMemoryStore.getState().selectedMemoryId).toBe('mem-01');
    });
  });

  it('closes drawer on ESC', async () => {
    // Pre-open the drawer
    useMemoryStore.setState((s) => ({
      ...s,
      isDetailDrawerOpen: true,
      selectedMemoryId: 'mem-01',
    }));

    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    await userEvent.keyboard('{Escape}');

    await waitFor(() => {
      expect(useMemoryStore.getState().isDetailDrawerOpen).toBe(false);
    });
  });

  it('shows memory detail content when drawer is open', async () => {
    useMemoryStore.setState((s) => ({
      ...s,
      isDetailDrawerOpen: true,
      selectedMemoryId: 'mem-01',
    }));

    render(<MemoryPage />);
    await waitFor(() => {
      // Title appears in both drawer header and table row; use getAllByText
      const titles = screen.getAllByText(mockMemoryEntry.title!);
      expect(titles.length).toBeGreaterThanOrEqual(1);
    });
    // Content only appears in drawer body (not table — table shows truncated snippet)
    await waitFor(() => {
      expect(screen.getByText(mockMemoryEntry.content)).toBeInTheDocument();
    });
  });
});

// ─── 8. Create memory drawer ───────────────────────────────────────────────

describe('MemoryPage — create memory drawer', () => {
  it('opens create drawer on New Memory button click', async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByTestId('create-memory-btn')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByTestId('create-memory-btn'));

    await waitFor(() => {
      expect(useMemoryStore.getState().isCreateDrawerOpen).toBe(true);
    });
  });

  it('shows validation error when content is empty', async () => {
    useMemoryStore.setState((s) => ({ ...s, isCreateDrawerOpen: true }));
    render(<MemoryPage />);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Submit without content
    await userEvent.click(screen.getByRole('button', { name: /save memory/i }));

    await waitFor(() => {
      expect(screen.getByText('Content is required')).toBeInTheDocument();
    });
  });

  it('submits successfully and closes drawer', async () => {
    useMemoryStore.setState((s) => ({ ...s, isCreateDrawerOpen: true }));
    render(<MemoryPage />);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    await userEvent.type(
      screen.getByPlaceholderText(/enter the memory content/i),
      'New decision about caching strategy.',
    );

    await userEvent.click(screen.getByRole('button', { name: /save memory/i }));

    await waitFor(() => {
      expect(useMemoryStore.getState().isCreateDrawerOpen).toBe(false);
    });
  });

  it('shows error message on create failure', async () => {
    server.use(
      http.post(`${BASE}/api/v1/memory/`, () => {
        return HttpResponse.json({ detail: 'Server error' }, { status: 500 });
      }),
    );

    useMemoryStore.setState((s) => ({ ...s, isCreateDrawerOpen: true }));
    render(<MemoryPage />);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    await userEvent.type(
      screen.getByPlaceholderText(/enter the memory content/i),
      'This will fail.',
    );
    await userEvent.click(screen.getByRole('button', { name: /save memory/i }));

    await waitFor(() => {
      expect(screen.getByText(/failed to create memory entry/i)).toBeInTheDocument();
    });
  });
});

// ─── 9. Create scenario dialog ─────────────────────────────────────────────

describe('MemoryPage — create scenario dialog', () => {
  it('opens scenario dialog from ScenarioList', async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new scenario/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /new scenario/i }));

    await waitFor(() => {
      expect(screen.getByText('New Scenario')).toBeInTheDocument();
    });
  });

  it('shows validation error when name is empty', async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new scenario/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /new scenario/i }));
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /create scenario/i }));

    await waitFor(() => {
      expect(screen.getByText('Name is required')).toBeInTheDocument();
    });
  });

  it('creates scenario successfully and closes dialog', async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new scenario/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /new scenario/i }));
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText('Name'), 'New Test Scenario');
    await userEvent.click(screen.getByRole('button', { name: /create scenario/i }));

    // Dialog should close
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  it('shows error on scenario creation failure', async () => {
    server.use(
      http.post(`${BASE}/api/v1/scenarios/`, () => {
        return HttpResponse.json({ detail: 'error' }, { status: 500 });
      }),
    );

    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new scenario/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole('button', { name: /new scenario/i }));
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText('Name'), 'Fail Scenario');
    await userEvent.click(screen.getByRole('button', { name: /create scenario/i }));

    await waitFor(() => {
      expect(screen.getByText(/failed to create scenario/i)).toBeInTheDocument();
    });
  });
});

// ─── 10. Scenario filter ───────────────────────────────────────────────────

describe('MemoryPage — scenario filter', () => {
  it('renders scenario chip button from API', async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      // Q4 Infrastructure appears in filter chip AND in table cells;
      // verify the chip button is present
      const elements = screen.getAllByText('Q4 Infrastructure');
      const chipButton = elements.find((el) => el.tagName.toLowerCase() === 'button');
      expect(chipButton).toBeTruthy();
    });
  });

  it('filters table when scenario chip is clicked', async () => {
    render(<MemoryPage />);
    await waitFor(() => {
      expect(screen.getByText('Adopt pgvector for semantic search')).toBeInTheDocument();
      const elements = screen.getAllByText('Q4 Infrastructure');
      const chipButton = elements.find((el) => el.tagName.toLowerCase() === 'button');
      expect(chipButton).toBeTruthy();
    });

    // Click the chip button (aria-pressed on the button in ScenarioList)
    const q4Elements = screen.getAllByText('Q4 Infrastructure');
    const chipButton = q4Elements.find((el) => el.tagName.toLowerCase() === 'button')!;
    await userEvent.click(chipButton);

    await waitFor(() => {
      expect(useMemoryStore.getState().filters.scenarioId).toBe('scn-01');
    });

    // mem-02 has no scenario, should be hidden after filter
    await waitFor(() => {
      expect(screen.queryByText('Database connection pool exhaustion')).not.toBeInTheDocument();
    });
  });
});
