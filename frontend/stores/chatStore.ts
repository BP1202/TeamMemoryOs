/**
 * Chat store — client-side message history assembled during the session.
 *
 * Rules (from FRONTEND_RULES.md):
 *   - Chat message history is assembled client-side here — this is the
 *     ONE legitimate use of Zustand for chat.
 *   - Do NOT store raw API responses as-is — messages are wrapped in
 *     ChatMessage with a client-generated id and timestamp.
 *   - React Query still owns the mutation lifecycle (loading, error).
 *   - This store owns: messages[], session options, streaming state, UI state.
 */

import { create } from 'zustand';
import type { ChatMessage, ChatSession } from '@typedefs/chat';

interface ChatStore {
  // ─── State ──────────────────────────────────────────────────────────────
  messages: ChatMessage[];
  session: ChatSession;

  /** Whether a streaming response is in progress. */
  isStreaming: boolean;

  /** ID of the message currently being streamed into. */
  streamingMessageId: string | null;

  /**
   * AbortController for the in-flight request.
   * Stored here so Stop Generating can abort it from any component.
   * NOTE: Not serializable — never persisted.
   */
  abortController: AbortController | null;

  // ─── Message actions ────────────────────────────────────────────────────

  /** Append any message (user or assistant) to the list. */
  addMessage: (message: ChatMessage) => void;

  /** Replace an existing message by id (e.g., resolve a loading placeholder). */
  updateMessage: (id: string, patch: Partial<ChatMessage>) => void;

  /** Remove a message by id (used to remove failed loading placeholders). */
  removeMessage: (id: string) => void;

  /** Clear all messages — start a new conversation. */
  clearMessages: () => void;

  // ─── Session actions ────────────────────────────────────────────────────

  setScenario: (scenarioId: string | null) => void;
  setUseHybrid: (value: boolean) => void;

  // ─── Streaming actions ──────────────────────────────────────────────────

  /** Begin tracking a streaming response. */
  startStreaming: (messageId: string, controller: AbortController) => void;

  /** Append a token to the streaming message content. */
  appendStreamToken: (token: string) => void;

  /** Mark streaming as finished and clear the controller. */
  stopStreaming: () => void;

  /** Abort the in-flight request and stop streaming. */
  abortStreaming: () => void;
}

export const useChatStore = create<ChatStore>()((set, get) => ({
  messages: [],
  session: {
    scenario_id: null,
    use_hybrid: false,
  },
  isStreaming: false,
  streamingMessageId: null,
  abortController: null,

  // ── Message actions ──────────────────────────────────────────────────────

  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  updateMessage: (id, patch) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, ...patch } : m,
      ),
    })),

  removeMessage: (id) =>
    set((state) => ({
      messages: state.messages.filter((m) => m.id !== id),
    })),

  clearMessages: () => set({ messages: [] }),

  // ── Session actions ──────────────────────────────────────────────────────

  setScenario: (scenarioId) =>
    set((state) => ({
      session: { ...state.session, scenario_id: scenarioId },
    })),

  setUseHybrid: (value) =>
    set((state) => ({
      session: { ...state.session, use_hybrid: value },
    })),

  // ── Streaming actions ────────────────────────────────────────────────────

  startStreaming: (messageId, controller) =>
    set({
      isStreaming: true,
      streamingMessageId: messageId,
      abortController: controller,
    }),

  appendStreamToken: (token) => {
    const { streamingMessageId } = get();
    if (!streamingMessageId) return;
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === streamingMessageId
          ? { ...m, content: m.content + token }
          : m,
      ),
    }));
  },

  stopStreaming: () =>
    set({
      isStreaming: false,
      streamingMessageId: null,
      abortController: null,
    }),

  abortStreaming: () => {
    const { abortController } = get();
    abortController?.abort();
    set({
      isStreaming: false,
      streamingMessageId: null,
      abortController: null,
    });
  },
}));
