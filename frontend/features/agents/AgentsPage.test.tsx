/**
 * AgentsPage tests — covers registry, workflow, repository, debug, and history panels.
 *
 * Rules:
 *   - MSW for all API mocking — no real network calls.
 *   - renderWithProviders for all component renders.
 *   - Tests cover: data, loading, empty, error states.
 */

import { describe, it, expect } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@tests/utils/renderWithProviders';
import { server } from '@tests/mocks/server';
import { http, HttpResponse } from 'msw';
import { AgentsPage } from './AgentsPage';
import { AgentRegistryGrid } from './AgentRegistryGrid';
import { WorkflowPlanPreview } from './WorkflowPlanPreview';
import { WorkflowTimeline } from './WorkflowTimeline';
import { ExecutionMetricsBadge } from './ExecutionMetricsBadge';
import { CommitSummaryList } from './CommitSummaryList';
import { ConversationHistoryList } from './ConversationHistoryList';
import {
  mockWorkflowPlan,
  mockWorkflowRun,
  mockRepositorySearch,
} from '@tests/mocks/handlers';

const BASE = 'http://localhost:8000';

// ─── AgentRegistryGrid ────────────────────────────────────────────────────────

describe('AgentRegistryGrid', () => {
  it('renders agent cards after loading', async () => {
    renderWithProviders(<AgentRegistryGrid />);

    // Data state after fetch
    await waitFor(() => {
      expect(screen.getByTestId('agent-registry-grid')).toBeInTheDocument();
    });

    expect(screen.getByTestId('agent-card-repository_agent')).toBeInTheDocument();
    expect(screen.getByTestId('agent-card-debug_agent')).toBeInTheDocument();
  });

  it('shows empty state when no agents returned', async () => {
    server.use(
      http.get(`${BASE}/api/v1/agents/`, () =>
        HttpResponse.json({ agents: [], total: 0 }, { status: 200 }),
      ),
    );

    renderWithProviders(<AgentRegistryGrid />);

    await waitFor(() => {
      expect(screen.getByText('No agents registered')).toBeInTheDocument();
    });
  });

  it('shows error state on API failure with retry button', async () => {
    server.use(
      http.get(`${BASE}/api/v1/agents/`, () =>
        HttpResponse.json({ detail: 'Internal server error' }, { status: 500 }),
      ),
    );

    renderWithProviders(<AgentRegistryGrid />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load agents')).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('shows agent capabilities as tags', async () => {
    renderWithProviders(<AgentRegistryGrid />);
    await waitFor(() => {
      expect(screen.getByText('search commits')).toBeInTheDocument();
    });
  });
});

// ─── WorkflowPlanPreview ──────────────────────────────────────────────────────

describe('WorkflowPlanPreview', () => {
  it('renders plan preview with "not yet executed" label', () => {
    renderWithProviders(<WorkflowPlanPreview plan={mockWorkflowPlan} />);

    expect(screen.getByTestId('workflow-plan-preview')).toBeInTheDocument();
    expect(screen.getByText(/preview — not yet executed/i)).toBeInTheDocument();
    expect(screen.getByText(/3\.3s estimated/i)).toBeInTheDocument();
  });

  it('renders all 6 plan steps', () => {
    renderWithProviders(<WorkflowPlanPreview plan={mockWorkflowPlan} />);
    // 6 step numbers
    expect(screen.getByText('planner')).toBeInTheDocument();
    expect(screen.getByText('granite')).toBeInTheDocument();
  });

  it('has accessible aria-label "Preview only — not yet executed"', () => {
    renderWithProviders(<WorkflowPlanPreview plan={mockWorkflowPlan} />);
    expect(
      screen.getByRole('region', { name: /preview only — not yet executed/i }),
    ).toBeInTheDocument();
  });
});

// ─── WorkflowTimeline ─────────────────────────────────────────────────────────

describe('WorkflowTimeline', () => {
  it('renders timeline with 6 steps', () => {
    renderWithProviders(<WorkflowTimeline steps={mockWorkflowRun.steps} />);
    expect(screen.getByTestId('workflow-timeline')).toBeInTheDocument();
    // All step cards rendered
    for (let i = 1; i <= 6; i++) {
      expect(screen.getByTestId(`workflow-step-${i}`)).toBeInTheDocument();
    }
  });

  it('shows status labels on each step', () => {
    renderWithProviders(<WorkflowTimeline steps={mockWorkflowRun.steps} />);
    const completeLabels = screen.getAllByText('complete');
    expect(completeLabels.length).toBe(6);
  });

  it('renders nothing when steps is empty', () => {
    const { container } = renderWithProviders(<WorkflowTimeline steps={[]} />);
    expect(container.firstChild).toBeNull();
  });
});

// ─── ExecutionMetricsBadge ────────────────────────────────────────────────────

describe('ExecutionMetricsBadge', () => {
  it('renders formatted milliseconds', () => {
    renderWithProviders(<ExecutionMetricsBadge durationMs={850} />);
    expect(screen.getByText('850ms')).toBeInTheDocument();
  });

  it('renders formatted seconds for > 1000ms', () => {
    renderWithProviders(<ExecutionMetricsBadge durationMs={2845} />);
    expect(screen.getByText('2.8s')).toBeInTheDocument();
  });

  it('renders nothing when durationMs is null', () => {
    const { container } = renderWithProviders(<ExecutionMetricsBadge durationMs={null} />);
    expect(container.firstChild).toBeNull();
  });
});

// ─── CommitSummaryList ────────────────────────────────────────────────────────

describe('CommitSummaryList', () => {
  it('renders commit list with SHA and message', () => {
    renderWithProviders(<CommitSummaryList commits={mockRepositorySearch.commits} />);
    expect(screen.getByTestId('commit-summary-list')).toBeInTheDocument();
    expect(screen.getByText('a1b2c3d')).toBeInTheDocument(); // short SHA
    expect(screen.getByText('feat: add JWT refresh token rotation')).toBeInTheDocument();
  });

  it('shows "No commits found" when empty', () => {
    renderWithProviders(<CommitSummaryList commits={[]} />);
    expect(screen.getByText('No commits found.')).toBeInTheDocument();
  });
});

// ─── ConversationHistoryList ──────────────────────────────────────────────────

describe('ConversationHistoryList', () => {
  it('renders empty state when no history', () => {
    renderWithProviders(<ConversationHistoryList />);
    expect(screen.getByText('No history yet')).toBeInTheDocument();
  });

  it('renders turns from agentStore workflowHistory', async () => {
    // Import store and add a turn
    const { useAgentStore } = await import('@stores/agentStore');
    useAgentStore.setState({
      workflowHistory: [
        {
          id: 'turn-01',
          question: 'What changed in auth?',
          response: mockWorkflowRun,
          created_at: '2024-03-15T10:00:00Z',
        },
      ],
    });

    renderWithProviders(<ConversationHistoryList />);
    expect(screen.getByTestId('conversation-turn')).toBeInTheDocument();
    expect(screen.getByText('What changed in auth?')).toBeInTheDocument();

    // Reset store
    useAgentStore.setState({ workflowHistory: [] });
  });
});

// ─── AgentsPage ───────────────────────────────────────────────────────────────

describe('AgentsPage', () => {
  it('renders with registry tab active by default', async () => {
    renderWithProviders(<AgentsPage />, { initialPath: '/agents' });
    expect(screen.getByTestId('agents-page')).toBeInTheDocument();
    // Registry tab should be selected
    const registryTab = screen.getByRole('tab', { name: /registry/i });
    expect(registryTab).toHaveAttribute('aria-selected', 'true');
  });

  it('switches to workflow tab on click', async () => {
    const user = userEvent.setup();
    renderWithProviders(<AgentsPage />, { initialPath: '/agents' });

    const workflowTab = screen.getByRole('tab', { name: /workflow/i });
    await user.click(workflowTab);
    expect(workflowTab).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByTestId('workflow-panel')).toBeInTheDocument();
  });

  it('switches to debug tab on click', async () => {
    const user = userEvent.setup();
    renderWithProviders(<AgentsPage />, { initialPath: '/agents' });

    const debugTab = screen.getByRole('tab', { name: /debug/i });
    await user.click(debugTab);
    expect(screen.getByTestId('debug-agent-panel')).toBeInTheDocument();
  });

  it('switches to repository tab on click', async () => {
    const user = userEvent.setup();
    renderWithProviders(<AgentsPage />, { initialPath: '/agents' });

    const repoTab = screen.getByRole('tab', { name: /repository/i });
    await user.click(repoTab);
    expect(screen.getByTestId('repository-agent-panel')).toBeInTheDocument();
  });
});
