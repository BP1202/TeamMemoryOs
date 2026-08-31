import { useState, useRef, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { UtilityIcons } from '@config/icons';
import { useAuthStore } from '@stores/authStore';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  code?: string;
  title?: string;
  isSaved?: boolean;
  timestamp: string;
}

const DEFAULT_WELCOME: ChatMessage = {
  id: 'welcome',
  role: 'assistant',
  content: 'Hello! I am your AI Engineering Co-worker. Ask any question about bugs, architecture, or paste an error trace to get a verified solution from your team memory.',
  timestamp: 'Today',
};

export function ChatPage() {
  const [searchParams] = useSearchParams();
  const user = useAuthStore((s) => s.user);
  const initialQuery = searchParams.get('q');

  // 1. Persistent Chat History in localStorage
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = localStorage.getItem('teammemory_chat_history');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (e) {
      // fallback
    }
    return [DEFAULT_WELCOME];
  });

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-trigger query from search params if provided
  useEffect(() => {
    if (initialQuery && initialQuery.trim()) {
      handleSendMessage(initialQuery.trim());
    }
  }, [initialQuery]);

  // Sync to localStorage on message update
  useEffect(() => {
    try {
      localStorage.setItem('teammemory_chat_history', JSON.stringify(messages));
    } catch (e) {
      // storage error
    }
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (queryText: string) => {
    const trimmed = queryText.trim();
    if (!trimmed || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: trimmed,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch('http://localhost:8000/api/v1/chat/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: trimmed }),
      });
      const data = await res.json();

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        title: data.title || 'Technical Resolution',
        content: `${data.summary || 'Here is the verified fix based on team knowledge.'}\n\n${data.why ? `**Root Cause:** ${data.why}` : ''}`,
        code: data.recommended_action || '',
        isSaved: false,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: `ai-err-${Date.now()}`,
        role: 'assistant',
        content: 'Could not connect to AI backend. Please verify FastAPI backend is running on port 8000.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    alert('Code copied to clipboard!');
  };

  // 2. Real Save to Backend AND Memory Book Store
  const handleSaveToMemory = async (msgId: string, title?: string, content?: string, code?: string) => {
    const memoryTitle = title || 'Engineering Resolution';
    const memoryCode = code || content || '';
    const memoryProblem = content || 'Resolved engineering issue.';

    // Save locally
    try {
      const existingSaved = JSON.parse(localStorage.getItem('teammemory_saved_memories') || '[]');
      const newMemoryItem = {
        id: `MEM-SAVED-${Date.now().toString().slice(-4)}`,
        title: memoryTitle,
        category: 'Backend',
        problem: memoryProblem,
        symptoms: memoryProblem.slice(0, 100),
        root_cause: 'Extracted directly from AI conversation session.',
        working_solution: 'Applied verified code patch.',
        code_patch: memoryCode,
        verified_by: user?.full_name || 'You (AI Assistant)',
        avatar: '✨',
        times_reused: 1,
        date: 'Just now',
        related_services: ['Backend API', 'Core Service'],
        related_memories: ['Verified Resolution'],
      };
      localStorage.setItem('teammemory_saved_memories', JSON.stringify([newMemoryItem, ...existingSaved]));
    } catch (e) {
      // storage error
    }

    // Call backend
    try {
      await fetch('http://localhost:8000/api/v1/incident/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: memoryTitle,
          classification: 'Engineering Memory',
          root_cause: memoryProblem,
          solution: memoryCode,
          services_affected: ['Backend API'],
        }),
      });
    } catch (e) {
      // pass
    }

    setMessages((prev) =>
      prev.map((m) => (m.id === msgId ? { ...m, isSaved: true } : m))
    );

    setSaveSuccessMsg(`🎉 "${memoryTitle}" saved to Memory Book! Open Memory Book to view.`);
    setTimeout(() => setSaveSuccessMsg(null), 4000);
  };

  const handleClearChat = () => {
    setMessages([DEFAULT_WELCOME]);
    localStorage.removeItem('teammemory_chat_history');
  };

  return (
    <div className="flex flex-col h-screen bg-[#0B0914] text-white font-sans">
      {/* Top Header */}
      <div className="h-16 border-b border-[#2D264E] px-6 flex items-center justify-between bg-[#141224] flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-2xl bg-[#8B5CF6]/20 border border-[#8B5CF6]/40 flex items-center justify-center text-[#C4B5FD] text-lg font-bold">
            🤖
          </div>
          <div>
            <h1 className="text-sm font-bold text-white flex items-center gap-2">
              AI Engineering Assistant
              <span className="text-[10px] font-mono bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 px-2 py-0.5 rounded-full">
                Persistent Chat
              </span>
            </h1>
            <p className="text-[11px] text-[#A5A0C8]">
              Ask bugs, architecture, APIs, or paste code traces
            </p>
          </div>
        </div>

        {/* Clear Chat Button */}
        <button
          onClick={handleClearChat}
          className="text-xs text-[#A5A0C8] hover:text-white px-3 py-1.5 rounded-xl border border-[#2D264E] hover:bg-[#1E1938] transition-all"
        >
          Clear Chat
        </button>
      </div>

      {/* Save Success Toast */}
      {saveSuccessMsg && (
        <div className="bg-emerald-950/80 border-b border-[#22C55E]/50 px-6 py-2.5 text-xs text-[#22C55E] font-bold text-center animate-fade-in flex items-center justify-center gap-2">
          <span>✨</span> {saveSuccessMsg}
        </div>
      )}

      {/* Messages Feed */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 max-w-4xl w-full mx-auto">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} space-y-1.5`}
          >
            {/* Role Header */}
            <div className="flex items-center gap-2 px-1 text-[11px] text-[#A5A0C8] font-mono">
              <span>{msg.role === 'user' ? 'You' : 'AI Assistant'}</span>
              <span>•</span>
              <span>{msg.timestamp}</span>
            </div>

            {/* Message Bubble */}
            {msg.role === 'user' ? (
              <div className="max-w-2xl px-5 py-3.5 bg-[#8B5CF6] text-white text-sm font-medium rounded-3xl rounded-tr-sm shadow-xl leading-relaxed whitespace-pre-wrap">
                {msg.content}
              </div>
            ) : (
              <div className="max-w-3xl w-full bg-[#141224] border border-[#2D264E] rounded-3xl rounded-tl-sm p-6 shadow-xl space-y-4">
                {msg.title && (
                  <h3 className="text-sm font-bold text-white pb-2 border-b border-[#2D264E] flex items-center justify-between">
                    <span>{msg.title}</span>
                    <span className="text-[10px] font-mono text-[#8B5CF6] bg-[#8B5CF6]/15 px-2 py-0.5 rounded-full border border-[#8B5CF6]/30">
                      Verified Fix
                    </span>
                  </h3>
                )}

                <div className="text-sm text-zinc-200 leading-relaxed whitespace-pre-wrap">
                  {msg.content}
                </div>

                {msg.code && (
                  <div className="space-y-2 pt-1">
                    <pre className="p-4 bg-[#0B0914] border border-[#2D264E] rounded-2xl font-mono text-xs text-zinc-200 overflow-x-auto">
                      <code>{msg.code}</code>
                    </pre>

                    {/* ONLY 2 BUTTONS: Copy Code & Save to Memory */}
                    <div className="flex items-center gap-3 pt-2">
                      <button
                        onClick={() => handleCopyCode(msg.code!)}
                        className="px-4 py-2 bg-[#1E1938] hover:bg-[#2D264F] border border-[#2D264E] text-white font-bold text-xs rounded-xl transition-all flex items-center gap-1.5"
                      >
                        <span>📋 Copy Code</span>
                      </button>

                      <button
                        onClick={() =>
                          handleSaveToMemory(msg.id, msg.title, msg.content, msg.code)
                        }
                        disabled={msg.isSaved}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                          msg.isSaved
                            ? 'bg-[#22C55E]/20 border border-[#22C55E]/40 text-[#22C55E]'
                            : 'bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white shadow-lg shadow-[#8B5CF6]/25'
                        }`}
                      >
                        <span>{msg.isSaved ? '✓ Saved to Memory Book' : '💾 Save to Memory'}</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center gap-3 p-4 bg-[#141224] border border-[#2D264E] rounded-3xl max-w-sm">
            <div className="h-4 w-4 border-2 border-[#8B5CF6] border-t-transparent rounded-full animate-spin" />
            <span className="text-xs text-[#C4B5FD] font-mono animate-pulse">
              AI searching memory & generating fix...
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Input Area */}
      <div className="p-4 md:p-6 border-t border-[#2D264E] bg-[#141224] flex-shrink-0">
        <div className="max-w-4xl mx-auto space-y-3">
          {/* Quick Suggestion Chips */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] text-[#A5A0C8] font-mono">Suggested:</span>
            {[
              'JWT 401 Unauthorized',
              'PostgreSQL Pool Timeout',
              'Redis Redlock Concurrency',
              'FastAPI CORS Header Blocked',
            ].map((chip) => (
              <button
                key={chip}
                onClick={() => handleSendMessage(chip)}
                className="px-2.5 py-1 bg-[#1E1938] hover:bg-[#2D264F] text-[11px] text-[#C4B5FD] rounded-lg border border-[#2D264E] transition-all"
              >
                {chip}
              </button>
            ))}
          </div>

          {/* Clean Input Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage(input);
            }}
            className="flex items-center gap-3"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything or paste an error trace..."
              disabled={isLoading}
              className="flex-1 bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-2xl px-5 py-3.5 text-sm text-white placeholder-zinc-500 focus:outline-none shadow-inner"
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="px-6 py-3.5 bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] disabled:opacity-40 text-white font-bold text-sm rounded-2xl shadow-lg shadow-[#8B5CF6]/25 transition-all flex items-center gap-2 flex-shrink-0"
            >
              <span>Send</span>
              <UtilityIcons.ArrowRight className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
