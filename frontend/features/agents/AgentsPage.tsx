/**
 * AgentsPage — Multi-Agent Workspace.
 *
 * Features (tabs):
 *   - Registry:   Browse registered agents.
 *   - Workflow:   Plan (dry-run) and execute multi-agent workflows.
 *   - Repository: Repository Agent search and file history.
 *   - Debug:      Debug Agent error + stack trace analysis.
 *   - History:    Per-session conversation history with agent attribution.
 *
 * Routing:
 *   /agents            → Registry tab active
 *   /agents/workflow   → Workflow tab active
 *   /agents/repository → Repository tab active
 *   /agents/debug      → Debug tab active
 *
 * Architecture:
 *   - useAgentStore drives activePanel (UI state).
 *   - Tabs set activePanel on click.
 *   - React Query owns all server state.
 */

import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { NavIcons, UtilityIcons } from '@config/icons';
import { useAgentStore } from '@stores/agentStore';
import { AgentRegistryGrid } from './AgentRegistryGrid';
import { WorkflowPanel } from './WorkflowPanel';
import { RepositoryAgentPanel } from './RepositoryAgentPanel';
import { DebugAgentPanel } from './DebugAgentPanel';
import { ConversationHistoryList } from './ConversationHistoryList';
import { cn } from '@utils/cn';
import type { AgentPanelTab } from '@typedefs/agents';

// ─── Tab definitions ──────────────────────────────────────────────────────────

interface Tab {
  id: AgentPanelTab;
  label: string;
  path: string;
}

const TABS: Tab[] = [
  { id: 'registry',   label: 'Registry',   path: '/agents' },
  { id: 'workflow',   label: 'Workflow',   path: '/agents/workflow' },
  { id: 'repository', label: 'Repository', path: '/agents/repository' },
  { id: 'debug',      label: 'Debug',      path: '/agents/debug' },
];

// ─── Path → tab ID resolution ─────────────────────────────────────────────────

function tabFromPath(path: string): AgentPanelTab {
  if (path.startsWith('/agents/workflow'))   return 'workflow';
  if (path.startsWith('/agents/repository')) return 'repository';
  if (path.startsWith('/agents/debug'))      return 'debug';
  return 'registry';
}

// ─── Component ────────────────────────────────────────────────────────────────

export function AgentsPage() {
  const location      = useLocation();
  const navigate      = useNavigate();
  const activePanel   = useAgentStore((s) => s.activePanel);
  const setActivePanel = useAgentStore((s) => s.setActivePanel);

  // Sync Zustand panel state with URL on mount and location change
  useEffect(() => {
    const tab = tabFromPath(location.pathname);
    setActivePanel(tab);
  }, [location.pathname, setActivePanel]);

  const handleTabClick = (tab: Tab) => {
    setActivePanel(tab.id);
    navigate(tab.path);
  };

  return (
    <div className="flex flex-col h-full" data-testid="agents-page">

      {/* ── Page header ─────────────────────────────────────────────────── */}
      <header className="flex items-center gap-3 px-6 py-4 border-b border-border flex-shrink-0">
        <div className="w-9 h-9 rounded-lg bg-purple-50 dark:bg-purple-900/20 flex items-center justify-center flex-shrink-0">
          <NavIcons.Agents className="h-5 w-5 text-purple-600 dark:text-purple-400" aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <h1 className="text-base font-semibold text-text-primary">
            Multi-Agent Workspace
          </h1>
          <p className="text-xs text-text-secondary truncate">
            Browse agents, run workflows, search repositories, and analyze errors.
          </p>
        </div>
      </header>

      {/* ── Tabs ────────────────────────────────────────────────────────── */}
      <nav
        className="flex gap-1 px-6 py-2 border-b border-border flex-shrink-0 overflow-x-auto"
        aria-label="Agent workspace tabs"
        role="tablist"
      >
        {TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activePanel === tab.id}
            aria-controls={`agent-panel-${tab.id}`}
            id={`agent-tab-${tab.id}`}
            type="button"
            onClick={() => handleTabClick(tab)}
            className={cn(
              'px-4 py-2 text-sm font-medium rounded-md whitespace-nowrap',
              'transition-colors duration-fast',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
              activePanel === tab.id
                ? 'bg-brand/10 text-brand'
                : 'text-text-secondary hover:text-text-primary hover:bg-surface-subtle',
            )}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* ── Panel content ───────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto min-h-0">
        <div className="flex gap-6 h-full">

          {/* ── Main panel ────────────────────────────────────────────── */}
          <main
            id={`agent-panel-${activePanel}`}
            role="tabpanel"
            aria-labelledby={`agent-tab-${activePanel}`}
            className="flex-1 min-w-0 px-6 py-6"
          >
            {activePanel === 'registry' && (
              <section aria-label="Agent Registry">
                <h2 className="text-sm font-semibold text-text-primary mb-4">
                  Registered Agents
                </h2>
                <AgentRegistryGrid />
              </section>
            )}

            {activePanel === 'workflow' && (
              <section aria-label="Workflow Execution">
                <h2 className="text-sm font-semibold text-text-primary mb-4">
                  Multi-Agent Workflow
                </h2>
                <WorkflowPanel />
              </section>
            )}

            {activePanel === 'repository' && (
              <section aria-label="Repository Agent">
                <RepositoryAgentPanel />
              </section>
            )}

            {activePanel === 'debug' && (
              <section aria-label="Debug Agent">
                <h2 className="text-sm font-semibold text-text-primary mb-4">
                  Debug Analysis
                </h2>
                <DebugAgentPanel />
              </section>
            )}
          </main>

          {/* ── Conversation history sidebar ─────────────────────────── */}
          <aside
            className={cn(
              'w-80 flex-shrink-0 border-l border-border px-4 py-6 overflow-y-auto',
              'hidden lg:block',
            )}
            aria-label="Workflow conversation history"
          >
            <ConversationHistoryList />
            <div className="mt-4 flex items-center gap-1 text-[10px] text-text-muted">
              <UtilityIcons.Filter className="h-3 w-3" aria-hidden="true" />
              <span>Session history — up to 20 turns</span>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
