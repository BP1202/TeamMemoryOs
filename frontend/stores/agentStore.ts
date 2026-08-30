/**
 * Agent store — client-side UI state for the Multi-Agent Workspace.
 *
 * Rules:
 *   - Only client UI state here — no server response data.
 *   - workflowHistory is assembled client-side (capped at 20 turns).
 *   - React Query owns server state and mutation lifecycle.
 */

import { create } from 'zustand';
import type { AgentPanelTab, WorkflowHistoryTurn } from '@typedefs/agents';

/** Maximum number of workflow history turns to retain. */
const MAX_HISTORY = 20;

interface AgentStore {
  // ─── State ────────────────────────────────────────────────────────────────
  /** Currently active panel tab. */
  activePanel: AgentPanelTab;

  /** Name of the currently selected/inspected agent (null = none). */
  selectedAgentName: string | null;

  /**
   * Workflow history — client-assembled turns, not raw API responses.
   * Capped at MAX_HISTORY (20) entries, oldest removed first.
   */
  workflowHistory: WorkflowHistoryTurn[];

  // ─── Actions ──────────────────────────────────────────────────────────────

  setActivePanel: (panel: AgentPanelTab) => void;
  setSelectedAgent: (name: string | null) => void;

  /** Prepend a workflow turn to history, capping at MAX_HISTORY. */
  addWorkflowTurn: (turn: WorkflowHistoryTurn) => void;

  /** Clear all workflow history turns. */
  clearWorkflowHistory: () => void;
}

export const useAgentStore = create<AgentStore>()((set) => ({
  activePanel: 'registry',
  selectedAgentName: null,
  workflowHistory: [],

  setActivePanel: (panel) => set({ activePanel: panel }),

  setSelectedAgent: (name) => set({ selectedAgentName: name }),

  addWorkflowTurn: (turn) =>
    set((state) => {
      const updated = [turn, ...state.workflowHistory];
      return { workflowHistory: updated.slice(0, MAX_HISTORY) };
    }),

  clearWorkflowHistory: () => set({ workflowHistory: [] }),
}));
