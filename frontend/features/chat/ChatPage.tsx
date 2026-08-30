/**
 * ChatPage — AI Chat Workspace.
 *
 * Features:
 *   - Full-screen chat interface.
 *   - Question submission to POST /api/v1/chat/ask via React Query mutation.
 *   - Message history assembled client-side in chatStore (Zustand).
 *   - All 5 explainability fields shown for every AI response.
 *   - Hybrid/semantic retrieval toggle in AIWorkspaceHeader.
 *   - Scenario filter.
 *   - Suggested actions as buttons.
 *   - Welcome screen with prompt chips on empty state.
 *   - Auto-scroll + floating "Scroll to bottom" button.
 *   - Clear conversation confirmation dialog.
 *   - Stop generating button while loading.
 *   - Loading, empty, and error states.
 *   - Accessible: role="log", aria-live, focus management.
 *
 * Architecture rules:
 *   - useMutation from React Query owns the network lifecycle.
 *   - chatStore owns the assembled message list + streaming state.
 *   - No direct axios calls in this component.
 *   - No dangerouslySetInnerHTML.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { NavIcons, UtilityIcons } from '@config/icons';
import { Button } from '@components/ui/Button';
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from '@components/ui/Dialog';
import { STALE_TIME_MEMORY } from '@config/constants';
import { useAuthStore } from '@stores/authStore';
import { useChatStore } from '@stores/chatStore';
import { askChat } from '@services/chatService';
import { listScenarios } from '@services/scenarioService';
import { SCENARIO_LIST_KEY } from '@features/memory/ScenarioList';
import { AIWorkspaceHeader } from './AIWorkspaceHeader';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import type { ChatMessage } from '@typedefs/chat';
import type { RetrievalModeOption } from './AIWorkspaceHeader';
import { cn } from '@utils/cn';

// ─── Suggested starter prompts shown on empty state ───────────────────────────

const STARTER_PROMPTS = [
  'What architectural decisions have we made recently?',
  'Summarize recent incidents and their root causes.',
  'What context exists around our authentication system?',
  'What technologies does our team use most?',
];

// ─── Deterministic client ID ───────────────────────────────────────────────

function generateMessageId(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

// ─── Component ──────────────────────────────────────────────────────────────

export function ChatPage() {
  const orgId = useAuthStore((s) => s.user?.id ?? '');
  const orgName = useAuthStore((s) => s.user?.full_name);

  const messages        = useChatStore((s) => s.messages);
  const session         = useChatStore((s) => s.session);
  const addMessage      = useChatStore((s) => s.addMessage);
  const updateMessage   = useChatStore((s) => s.updateMessage);
  const clearMessages   = useChatStore((s) => s.clearMessages);
  const setScenario     = useChatStore((s) => s.setScenario);
  const setUseHybrid    = useChatStore((s) => s.setUseHybrid);
  const startStreaming  = useChatStore((s) => s.startStreaming);
  const stopStreaming   = useChatStore((s) => s.stopStreaming);
  const abortStreaming  = useChatStore((s) => s.abortStreaming);

  const messagesEndRef   = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const [clearDialogOpen, setClearDialogOpen] = useState(false);

  // Derived retrieval mode for AIWorkspaceHeader
  const retrievalMode: RetrievalModeOption = session.use_hybrid ? 'hybrid' : 'semantic';

  // ─── Scenario list for the filter ──────────────────────────────────────

  const scenariosQ = useQuery({
    queryKey: SCENARIO_LIST_KEY(orgId),
    queryFn:  () => listScenarios(orgId),
    staleTime: STALE_TIME_MEMORY,
    enabled:  Boolean(orgId),
  });

  // ─── Chat mutation ─────────────────────────────────────────────────────

  const chatMutation = useMutation({
    mutationFn: (payload: { request: Parameters<typeof askChat>[0]; signal: AbortSignal }) =>
      askChat(payload.request, payload.signal),
  });

  // ─── Scroll management ─────────────────────────────────────────────────

  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  }, []);

  // Auto-scroll on new messages
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Show scroll-to-bottom button when user has scrolled up
  const handleScroll = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) return;
    const distFromBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight;
    setShowScrollBtn(distFromBottom > 120);
  }, []);

  // ─── Submit handler ────────────────────────────────────────────────────

  const handleSend = useCallback((text: string) => {
    // 1. Add user message immediately
    const userMessage: ChatMessage = {
      id: generateMessageId(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
      explanation: null,
    };
    addMessage(userMessage);

    // 2. Add a loading placeholder for the assistant
    const placeholderId = generateMessageId();
    const placeholder: ChatMessage = {
      id: placeholderId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      explanation: null,
      isLoading: true,
    };
    addMessage(placeholder);

    // 3. Create AbortController for this request
    const controller = new AbortController();
    startStreaming(placeholderId, controller);

    // 4. Fire the mutation
    chatMutation.mutate(
      {
        request: {
          organization_id: orgId,
          question:        text,
          top_k:           5,
          scenario_id:     session.scenario_id,
          use_hybrid:      session.use_hybrid,
        },
        signal: controller.signal,
      },
      {
        onSuccess: (response) => {
          updateMessage(placeholderId, {
            content:    response.answer,
            isLoading:  false,
            explanation: response.explanation ?? null,
          });
          stopStreaming();
        },
        onError: (err) => {
          const isAbort = err instanceof Error && err.name === 'CanceledError';
          updateMessage(placeholderId, {
            isLoading: false,
            error: isAbort
              ? 'Generation stopped.'
              : (err instanceof Error ? err.message : 'Failed to get a response.'),
          });
          stopStreaming();
        },
      },
    );
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId, session, addMessage, updateMessage, startStreaming, stopStreaming]);

  // ─── Suggested action / prompt chip handler ────────────────────────────

  const handleSuggestedAction = useCallback((action: string) => {
    handleSend(action);
  }, [handleSend]);

  // ─── Clear with confirmation ───────────────────────────────────────────

  const handleConfirmedClear = () => {
    clearMessages();
    setClearDialogOpen(false);
  };

  // ─── Retrieval mode toggle ─────────────────────────────────────────────

  const handleRetrievalModeChange = (mode: RetrievalModeOption) => {
    setUseHybrid(mode === 'hybrid');
  };

  // ─── Render ────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-full" data-testid="chat-page">

      {/* ── Header (AIWorkspaceHeader) ────────────────────────────────── */}
      <AIWorkspaceHeader
        title="AI Chat"
        description="Ask questions about your team's organizational memory."
        icon={NavIcons.Chat}
        organizationName={orgName ?? undefined}
        retrievalMode={retrievalMode}
        onRetrievalModeChange={handleRetrievalModeChange}
        hasConversation={messages.length > 0}
        onClear={() => setClearDialogOpen(true)}
        isLoading={chatMutation.isPending}
      />

      {/* ── Message list ──────────────────────────────────────────────── */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-6 min-h-0 relative"
        role="log"
        aria-live="polite"
        aria-label="Conversation messages"
        data-testid="message-list"
      >
        {/* Welcome / empty state */}
        {messages.length === 0 && (
          <div
            className="flex flex-col items-center justify-center h-full gap-6 py-16 text-center"
            data-testid="welcome-screen"
          >
            <div className="space-y-2">
              <div
                className="w-12 h-12 rounded-xl bg-brand/10 flex items-center justify-center mx-auto"
                aria-hidden="true"
              >
                <NavIcons.Chat className="h-6 w-6 text-brand" aria-hidden="true" />
              </div>
              <h2 className="text-lg font-semibold text-text-primary">
                Start a conversation
              </h2>
              <p className="text-sm text-text-secondary max-w-sm">
                Ask anything about your team's decisions, context, incidents, and
                organizational knowledge.
              </p>
            </div>

            {/* Starter prompt chips */}
            <div
              className="flex flex-wrap gap-2 justify-center max-w-lg"
              aria-label="Suggested starter questions"
            >
              {STARTER_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => handleSuggestedAction(prompt)}
                  className={cn(
                    'px-3 py-2 text-xs rounded-lg border border-border',
                    'bg-surface-subtle text-text-secondary text-left',
                    'hover:bg-surface-elevated hover:text-text-primary transition-colors',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
                  )}
                  aria-label={`Ask: ${prompt}`}
                  data-testid="starter-prompt"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message thread */}
        {messages.length > 0 && (
          <div className="space-y-6 max-w-3xl mx-auto">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onSuggestedAction={handleSuggestedAction}
              />
            ))}
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} aria-hidden="true" />

        {/* Floating scroll-to-bottom button */}
        {showScrollBtn && (
          <button
            type="button"
            onClick={() => scrollToBottom()}
            className={cn(
              'fixed bottom-28 right-8 z-10',
              'w-9 h-9 rounded-full shadow-lg',
              'bg-surface-elevated border border-border text-text-secondary',
              'hover:text-text-primary hover:bg-surface-subtle transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
              'flex items-center justify-center',
            )}
            aria-label="Scroll to latest message"
            data-testid="scroll-to-bottom-btn"
          >
            <UtilityIcons.ChevronDown className="h-4 w-4" aria-hidden="true" />
          </button>
        )}
      </div>

      {/* ── Stop generating button ────────────────────────────────────── */}
      {chatMutation.isPending && (
        <div className="flex justify-center py-2 flex-shrink-0">
          <Button
            variant="secondary"
            size="sm"
            onClick={abortStreaming}
            aria-label="Stop generating response"
            data-testid="stop-generating-btn"
          >
            <UtilityIcons.Close className="h-3.5 w-3.5" aria-hidden="true" />
            Stop generating
          </Button>
        </div>
      )}

      {/* ── Chat input ────────────────────────────────────────────────── */}
      <div className="flex-shrink-0">
        <ChatInput
          onSubmit={handleSend}
          isLoading={chatMutation.isPending}
          scenarios={scenariosQ.data ?? []}
          selectedScenarioId={session.scenario_id}
          useHybrid={session.use_hybrid}
          onScenarioChange={setScenario}
          onHybridChange={setUseHybrid}
        />
      </div>

      {/* ── Clear confirmation dialog ─────────────────────────────────── */}
      <Dialog open={clearDialogOpen} onOpenChange={setClearDialogOpen}>
        <DialogContent aria-labelledby="clear-dialog-title">
          <DialogTitle id="clear-dialog-title">
            Clear conversation?
          </DialogTitle>
          <DialogDescription>
            This will permanently remove all messages in this session. This
            action cannot be undone.
          </DialogDescription>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="secondary" size="sm">
                Cancel
              </Button>
            </DialogClose>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleConfirmedClear}
              data-testid="confirm-clear-btn"
            >
              Clear conversation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
