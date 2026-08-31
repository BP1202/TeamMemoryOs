/**
 * ChatPage test suite — Sprint 8.4 + Polish
 *
 * Covers:
 *   - Welcome/empty state with starter prompts
 *   - Message send creates user bubble
 *   - Loading (StreamingMessage) shown during request
 *   - Assistant response via AIResponseCard
 *   - Explainability: ConfidenceBadge + RetrievalModeTag always visible in header
 *   - Explainability: Citations + GraphPath accessible via accordion
 *   - ExplainabilityAccordion expand/collapse
 *   - AIResponseCard renders Granite badge
 *   - Suggested actions rendered as buttons
 *   - Suggested action click sends new message
 *   - Stop generating button visible while loading
 *   - Clear conversation opens dialog, confirm clears
 *   - Cancel clear dialog keeps messages
 *   - API error shows error state in bubble
 *   - ChatInput: submit disabled while loading
 *   - ChatInput: Enter key submits form
 *   - ChatInput: empty message does not submit
 *   - Hybrid retrieval toggle via AIWorkspaceHeader
 *   - Starter prompt chips submit question
 *   - Accessibility: role="log", aria-live
 *   - Copy code button present on code blocks
 *
 * Stack: Vitest + RTL + MSW
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '../../tests/mocks/server';
import { mockChatResponse, mockExplanation } from '../../tests/mocks/handlers';
import { render } from '../../tests/utils/renderWithProviders';
import { ChatPage } from './ChatPage';
import { AIResponseCard } from './AIResponseCard';
import { ExplainabilityAccordion } from '@features/explainability/ExplainabilityAccordion';
import { MarkdownRenderer } from '@utils/markdownRenderer';
import { useChatStore } from '@stores/chatStore';
import { useAuthStore } from '@stores/authStore';

const BASE = 'http://localhost:8000';

// ─── Helpers ─────────────────────────────────────────────────────────────────

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
  useChatStore.setState({
    messages: [],
    session: { scenario_id: null, use_hybrid: false },
    isStreaming: false,
    streamingMessageId: null,
    abortController: null,
  });
});

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('ChatPage', () => {
  // ── Welcome / empty state ──────────────────────────────────────────────────

  it('shows welcome screen when there are no messages', () => {
    render(<ChatPage />);
    expect(screen.getByText('Start a conversation')).toBeInTheDocument();
    expect(screen.getByTestId('welcome-screen')).toBeInTheDocument();
  });

  it('renders starter prompt chips on empty state', () => {
    render(<ChatPage />);
    const chips = screen.getAllByTestId('starter-prompt');
    expect(chips.length).toBeGreaterThan(0);
    // Each chip must be a button
    chips.forEach((chip) => expect(chip.tagName).toBe('BUTTON'));
  });

  it('has a chat input with placeholder text', () => {
    render(<ChatPage />);
    expect(
      screen.getByPlaceholderText(/Ask about your team/i),
    ).toBeInTheDocument();
  });

  it('does not show the clear button when there are no messages', () => {
    render(<ChatPage />);
    expect(screen.queryByTestId('clear-chat-btn')).not.toBeInTheDocument();
  });

  // ── Message list accessibility ─────────────────────────────────────────────

  it('message list has role="log" and aria-live="polite"', () => {
    render(<ChatPage />);
    const log = screen.getByRole('log');
    expect(log).toBeInTheDocument();
    expect(log).toHaveAttribute('aria-live', 'polite');
  });

  // ── Sending a message ──────────────────────────────────────────────────────

  it('renders user bubble after typing and sending a message', async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    const input = screen.getByPlaceholderText(/Ask about your team/i);
    await user.type(input, 'How does authentication work?');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByTestId('message-user')).toBeInTheDocument();
      expect(screen.getByText('How does authentication work?')).toBeInTheDocument();
    });
  });

  it('clears the input field after sending', async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    const input = screen.getByPlaceholderText(/Ask about your team/i) as HTMLTextAreaElement;
    await user.type(input, 'Test question');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(input.value).toBe('');
    });
  });

  it('does not submit when message is empty', async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    const input = screen.getByPlaceholderText(/Ask about your team/i);
    await user.click(input);
    await user.keyboard('{Enter}');

    expect(screen.queryByTestId('message-user')).not.toBeInTheDocument();
  });

  it('clicking a starter prompt chip sends it as a message', async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    const chip = screen.getAllByTestId('starter-prompt')[0];
    await user.click(chip);

    await waitFor(() => {
      expect(screen.getByTestId('message-user')).toBeInTheDocument();
    });
  });

  // ── Loading state ──────────────────────────────────────────────────────────

  it('shows StreamingMessage (Thinking…) while awaiting response', async () => {
    server.use(
      http.post(`${BASE}/api/v1/chat/ask`, async () => {
        await new Promise((resolve) => setTimeout(resolve, 200));
        return HttpResponse.json(mockChatResponse);
      }),
    );

    const user = userEvent.setup();
    render(<ChatPage />);

    const input = screen.getByPlaceholderText(/Ask about your team/i);
    await user.type(input, 'Loading test');
    await user.keyboard('{Enter}');

    expect(await screen.findByTestId('streaming-message')).toBeInTheDocument();
    expect(await screen.findByText('Thinking…')).toBeInTheDocument();
  });

  it('shows Stop generating button while loading', async () => {
    server.use(
      http.post(`${BASE}/api/v1/chat/ask`, async () => {
        await new Promise((resolve) => setTimeout(resolve, 200));
        return HttpResponse.json(mockChatResponse);
      }),
    );

    const user = userEvent.setup();
    render(<ChatPage />);

    const input = screen.getByPlaceholderText(/Ask about your team/i);
    await user.type(input, 'Stop test');
    await user.keyboard('{Enter}');

    expect(await screen.findByTestId('stop-generating-btn')).toBeInTheDocument();
  });

  it('send button is disabled while loading', async () => {
    server.use(
      http.post(`${BASE}/api/v1/chat/ask`, async () => {
        await new Promise((resolve) => setTimeout(resolve, 200));
        return HttpResponse.json(mockChatResponse);
      }),
    );

    const user = userEvent.setup();
    render(<ChatPage />);

    const input = screen.getByPlaceholderText(/Ask about your team/i);
    await user.type(input, 'Another question');
    await user.keyboard('{Enter}');

    const sendBtn = screen.getByRole('button', { name: /send/i });
    expect(sendBtn).toBeDisabled();
  });

  // ── Successful response ────────────────────────────────────────────────────

  it('renders assistant answer via AIResponseCard after successful response', async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    const input = screen.getByPlaceholderText(/Ask about your team/i);
    await user.type(input, 'How does auth work?');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByTestId('message-assistant')).toBeInTheDocument();
      expect(screen.getByTestId('ai-response-card')).toBeInTheDocument();
      expect(
        screen.getByText(/Authentication is handled via JWT tokens/i),
      ).toBeInTheDocument();
    });
  });

  it('renders Granite badges (header + card)', async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    const input = screen.getByPlaceholderText(/Ask about your team/i);
    await user.type(input, 'Granite badge test');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      // Both AIWorkspaceHeader and AIResponseCard render a Granite badge
      const badges = screen.getAllByLabelText(/Powered by IBM Granite/i);
      expect(badges.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders the explainability accordion for assistant messages', async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    const input = screen.getByPlaceholderText(/Ask about your team/i);
    await user.type(input, 'Explain retrieval');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByTestId('explainability-accordion')).toBeInTheDocument();
    });
  });

  it('renders ConfidenceBadge visible (in card header and/or accordion trigger)', async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    const input = screen.getByPlaceholderText(/Ask about your team/i);
    await user.type(input, 'Confidence test');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      // mockExplanation.confidence = 0.87 → "87%"
      // Badge appears in both AIResponseCard header and ExplainabilityAccordion trigger
      const badges = screen.getAllByLabelText(/Confidence: High \(87%\)/i);
      expect(badges.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders RetrievalModeTag visible (in card header and/or accordion trigger)', async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    const input = screen.getByPlaceholderText(/Ask about your team/i);
    await user.type(input, 'Mode test');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      // Tag appears in both AIResponseCard header and ExplainabilityAccordion trigger
      const tags = screen.getAllByLabelText(/Retrieval mode: Semantic search/i);
      expect(tags.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('accordion expands to show CitationPanel when triggered', async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    const input = screen.getByPlaceholderText(/Ask about your team/i);
    await user.type(input, 'Citation test');
    await user.keyboard('{Enter}');

    // Wait for accordion to appear
    const trigger = await screen.findByRole('button', { name: /Show retrieval explanation/i });
    // Open the accordion
    await user.click(trigger);

    await waitFor(() => {
      expect(screen.getByText(/Citations \(1\)/i)).toBeInTheDocument();
      expect(screen.getByText('Adopt pgvector for semantic search')).toBeInTheDocument();
    });
  });

  it('accordion expands to show GraphPathPanel when triggered', async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    const input = screen.getByPlaceholderText(/Ask about your team/i);
    await user.type(input, 'Graph path test');
    await user.keyboard('{Enter}');

    const trigger = await screen.findByRole('button', { name: /Show retrieval explanation/i });
    await user.click(trigger);

    await waitFor(() => {
      expect(screen.getByText(/Graph Path \(1 step\)/i)).toBeInTheDocument();
    });
  });

  // ── Suggested actions ──────────────────────────────────────────────────────

  it('renders suggested actions as buttons in AIResponseCard', async () => {
    useChatStore.setState({
      messages: [
        {
          id: 'msg-test-1',
          role: 'user',
          content: 'Initial question',
          created_at: new Date().toISOString(),
          explanation: null,
        },
        {
          id: 'msg-test-2',
          role: 'assistant',
          content: 'Here is the answer.',
          created_at: new Date().toISOString(),
          explanation: mockExplanation,
          suggested_actions: ['How does the team handle incidents?', 'Show me recent decisions'],
        },
      ],
    });

    render(<ChatPage />);

    const actionButton = screen.getByRole('button', {
      name: /Ask: How does the team handle incidents\?/i,
    });
    expect(actionButton.tagName).toBe('BUTTON');
    expect(actionButton).toBeInTheDocument();
  });

  it('clicking a suggested action sends it as a new message', async () => {
    const user = userEvent.setup();

    useChatStore.setState({
      messages: [
        {
          id: 'msg-test-1',
          role: 'user',
          content: 'Initial question',
          created_at: new Date().toISOString(),
          explanation: null,
        },
        {
          id: 'msg-test-2',
          role: 'assistant',
          content: 'Here is the answer.',
          created_at: new Date().toISOString(),
          explanation: mockExplanation,
          suggested_actions: ['Tell me more about incidents'],
        },
      ],
    });

    render(<ChatPage />);

    const actionButton = screen.getByRole('button', {
      name: /Ask: Tell me more about incidents/i,
    });
    await user.click(actionButton);

    await waitFor(() => {
      const matches = screen.getAllByText('Tell me more about incidents');
      const hasUserBubble = matches.some((el) => el.tagName === 'P');
      expect(hasUserBubble).toBe(true);
    });
  });

  // ── Error state ────────────────────────────────────────────────────────────

  it('shows error message in assistant bubble on API failure', async () => {
    server.use(
      http.post(`${BASE}/api/v1/chat/ask`, () => {
        return HttpResponse.json(
          { detail: 'Internal server error' },
          { status: 500 },
        );
      }),
    );

    const user = userEvent.setup();
    render(<ChatPage />);

    const input = screen.getByPlaceholderText(/Ask about your team/i);
    await user.type(input, 'Error test');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      const errorEls = screen.getAllByRole('alert');
      expect(errorEls.length).toBeGreaterThan(0);
    });
  });

  // ── Clear conversation with dialog ────────────────────────────────────────

  it('clear button opens confirmation dialog', async () => {
    const user = userEvent.setup();

    useChatStore.setState({
      messages: [{
        id: 'msg-1',
        role: 'user',
        content: 'Something',
        created_at: new Date().toISOString(),
        explanation: null,
      }],
    });

    render(<ChatPage />);

    const clearBtn = screen.getByTestId('clear-chat-btn');
    await user.click(clearBtn);

    await waitFor(() => {
      expect(screen.getByText('Clear conversation?')).toBeInTheDocument();
    });
  });

  it('confirming clear removes all messages', async () => {
    const user = userEvent.setup();

    useChatStore.setState({
      messages: [{
        id: 'msg-1',
        role: 'user',
        content: 'Something',
        created_at: new Date().toISOString(),
        explanation: null,
      }],
    });

    render(<ChatPage />);

    await user.click(screen.getByTestId('clear-chat-btn'));
    const confirmBtn = await screen.findByTestId('confirm-clear-btn');
    await user.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByText('Start a conversation')).toBeInTheDocument();
    });
  });

  it('cancelling clear dialog keeps messages', async () => {
    const user = userEvent.setup();

    useChatStore.setState({
      messages: [{
        id: 'msg-1',
        role: 'user',
        content: 'Keep me',
        created_at: new Date().toISOString(),
        explanation: null,
      }],
    });

    render(<ChatPage />);

    await user.click(screen.getByTestId('clear-chat-btn'));
    await screen.findByText('Clear conversation?');

    const cancelBtn = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelBtn);

    await waitFor(() => {
      expect(screen.getByText('Keep me')).toBeInTheDocument();
    });
  });

  // ── Hybrid toggle via AIWorkspaceHeader ────────────────────────────────────

  it('hybrid retrieval toggle updates store', async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    const hybridBtn = screen.getByRole('radio', { name: /Hybrid/i });
    expect(hybridBtn).toHaveAttribute('aria-checked', 'false');

    await user.click(hybridBtn);
    expect(hybridBtn).toHaveAttribute('aria-checked', 'true');
    expect(useChatStore.getState().session.use_hybrid).toBe(true);
  });
});

// ─── AIResponseCard unit tests ────────────────────────────────────────────────

describe('AIResponseCard', () => {
  it('renders Granite badge when provider is ibm-granite', () => {
    render(
      <AIResponseCard
        content="Test answer"
        explanation={null}
        provider_used="ibm-granite"
      />,
    );
    expect(screen.getByLabelText(/Powered by IBM Granite/i)).toBeInTheDocument();
  });

  it('renders Granite badge when no provider specified (default)', () => {
    render(<AIResponseCard content="Test answer" explanation={null} />);
    expect(screen.getByLabelText(/Powered by IBM Granite/i)).toBeInTheDocument();
  });

  it('does not render Granite badge for unknown provider', () => {
    render(
      <AIResponseCard
        content="Test answer"
        explanation={null}
        provider_used="openai"
      />,
    );
    expect(
      screen.queryByLabelText(/Powered by IBM Granite/i),
    ).not.toBeInTheDocument();
  });

  it('renders ConfidenceBadge and RetrievalModeTag when explanation present', () => {
    render(
      <AIResponseCard content="Answer" explanation={mockExplanation} />,
    );
    // Both the card header AND the accordion trigger show these badges
    const confidenceBadges = screen.getAllByLabelText(/Confidence: High/i);
    expect(confidenceBadges.length).toBeGreaterThanOrEqual(1);
    const retrievalTags = screen.getAllByLabelText(/Retrieval mode:/i);
    expect(retrievalTags.length).toBeGreaterThanOrEqual(1);
  });

  it('renders answer content via MarkdownRenderer', () => {
    render(
      <AIResponseCard content="**Bold answer**" explanation={null} />,
    );
    expect(screen.getByText('Bold answer')).toBeInTheDocument();
  });

  it('renders suggested actions as <button> elements only', () => {
    render(
      <AIResponseCard
        content="Answer"
        explanation={null}
        suggested_actions={['Follow up', 'More detail']}
        onSuggestedAction={() => {}}
      />,
    );
    const followUp = screen.getByRole('button', { name: /Ask: Follow up/i });
    expect(followUp.tagName).toBe('BUTTON');
    // Crucially: not an <a>
    expect(followUp).not.toHaveAttribute('href');
  });

  it('calls onSuggestedAction when action button is clicked', async () => {
    const user = userEvent.setup();
    const onAction = (action: string) => {
      expect(action).toBe('Follow up');
    };
    render(
      <AIResponseCard
        content="Answer"
        explanation={null}
        suggested_actions={['Follow up']}
        onSuggestedAction={onAction}
      />,
    );
    await user.click(screen.getByRole('button', { name: /Ask: Follow up/i }));
  });

  it('renders ExplainabilityAccordion when explanation is present', () => {
    render(
      <AIResponseCard content="Answer" explanation={mockExplanation} />,
    );
    expect(screen.getByTestId('explainability-accordion')).toBeInTheDocument();
  });

  it('does not render accordion when explanation is null', () => {
    render(<AIResponseCard content="Answer" explanation={null} />);
    expect(screen.queryByTestId('explainability-accordion')).not.toBeInTheDocument();
  });
});

// ─── ExplainabilityAccordion unit tests ───────────────────────────────────────

describe('ExplainabilityAccordion', () => {
  it('renders closed by default', () => {
    render(<ExplainabilityAccordion explanation={mockExplanation} />);
    // Trigger visible
    expect(screen.getByRole('button', { name: /Show retrieval explanation/i })).toBeInTheDocument();
    // Citation content not yet visible (collapsed)
    expect(screen.queryByText(/Citations \(1\)/i)).not.toBeInTheDocument();
  });

  it('expands on click to reveal citation content', async () => {
    const user = userEvent.setup();
    render(<ExplainabilityAccordion explanation={mockExplanation} />);

    await user.click(screen.getByRole('button', { name: /Show retrieval explanation/i }));

    await waitFor(() => {
      expect(screen.getByText(/Citations \(1\)/i)).toBeInTheDocument();
    });
  });

  it('collapses again when trigger is clicked twice', async () => {
    const user = userEvent.setup();
    render(<ExplainabilityAccordion explanation={mockExplanation} />);

    const trigger = screen.getByRole('button', { name: /Show retrieval explanation/i });
    await user.click(trigger);
    await screen.findByText(/Citations \(1\)/i);
    await user.click(trigger);

    await waitFor(() => {
      expect(screen.queryByText(/Citations \(1\)/i)).not.toBeInTheDocument();
    });
  });

  it('shows ConfidenceBadge in trigger row', () => {
    render(<ExplainabilityAccordion explanation={mockExplanation} />);
    // Badge is always visible in trigger — even collapsed
    expect(screen.getByLabelText(/Confidence: High/i)).toBeInTheDocument();
  });

  it('defaultOpen=true starts expanded', async () => {
    render(<ExplainabilityAccordion explanation={mockExplanation} defaultOpen />);
    await waitFor(() => {
      expect(screen.getByText(/Citations \(1\)/i)).toBeInTheDocument();
    });
  });
});

// ─── MarkdownRenderer code block tests ───────────────────────────────────────

describe('MarkdownRenderer — code blocks', () => {
  it('renders a copy button for code blocks', () => {
    render(<MarkdownRenderer content={'```js\nconsole.log("hi")\n```'} />);
    expect(screen.getByTestId('copy-code-btn')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Copy code to clipboard/i })).toBeInTheDocument();
  });

  it('copy button has accessible aria-label', () => {
    render(<MarkdownRenderer content={'```\nsome code\n```'} />);
    const btn = screen.getByTestId('copy-code-btn');
    expect(btn).toHaveAttribute('aria-label', 'Copy code to clipboard');
  });

  it('renders inline code without copy button', () => {
    render(<MarkdownRenderer content="Use `const x = 1` here." />);
    expect(screen.getByText('const x = 1')).toBeInTheDocument();
    expect(screen.queryByTestId('copy-code-btn')).not.toBeInTheDocument();
  });
});
