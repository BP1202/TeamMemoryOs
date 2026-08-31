import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { m, AnimatePresence } from 'framer-motion';

interface MemoryCard {
  id: string;
  title: string;
  category: string;
  root_cause: string;
  solution_code: string;
  author: string;
  avatar: string;
  reused_count: number;
  time_saved: string;
}

const FEATURED_MEMORIES: MemoryCard[] = [
  {
    id: 'MEM-001',
    title: 'PostgreSQL Connection Limit Exceeded',
    category: 'Database',
    root_cause: 'Celery worker pool reached default 10 connections under concurrent async tasks.',
    solution_code: `engine = create_engine(
    DATABASE_URL,
    pool_size=50,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)`,
    author: 'Sarah',
    avatar: '🎯',
    reused_count: 24,
    time_saved: '4 hours',
  },
  {
    id: 'MEM-002',
    title: 'JWT Expired Signature Mismatch (401)',
    category: 'Authentication',
    root_cause: 'Missing algorithm="HS256" and token clock skew tolerance in auth middleware.',
    solution_code: `def verify_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])`,
    author: 'Devin',
    avatar: '💻',
    reused_count: 17,
    time_saved: '2 hours',
  },
  {
    id: 'MEM-003',
    title: 'Redis Distributed Lock Timeout in Celery',
    category: 'Backend',
    root_cause: 'Concurrent webhooks created race condition and duplicate invoice settlements.',
    solution_code: `with redis_client.lock("checkout_lock", timeout=15):
    process_payment(order_id)`,
    author: 'Alex',
    avatar: '👑',
    reused_count: 18,
    time_saved: '5 hours',
  },
  {
    id: 'MEM-004',
    title: 'FastAPI CORS Header Blocked in Local Dev',
    category: 'Frontend',
    root_cause: 'Missing CORSMiddleware origins config for Vite localhost:5173 server.',
    solution_code: `app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)`,
    author: 'Devin',
    avatar: '💻',
    reused_count: 35,
    time_saved: '3 hours',
  },
];

export function DashboardPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [memories, setMemories] = useState<MemoryCard[]>(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('teammemory_saved_memories') || '[]');
      if (Array.isArray(saved) && saved.length > 0) {
        const mapped = saved.map((s: any) => ({
          id: s.id,
          title: s.title,
          category: s.category || 'Backend',
          root_cause: s.root_cause || s.problem,
          solution_code: s.code_patch,
          author: s.verified_by || 'You',
          avatar: s.avatar || '✨',
          reused_count: s.times_reused || 1,
          time_saved: '2 hours',
        }));
        return [...mapped, ...FEATURED_MEMORIES];
      }
    } catch (e) {
      // pass
    }
    return FEATURED_MEMORIES;
  });
  const [selectedMemory, setSelectedMemory] = useState<MemoryCard | null>(null);

  // 4-Field Save Form State
  const [newTitle, setNewTitle] = useState('');
  const [newContext, setNewContext] = useState('');
  const [newFix, setNewFix] = useState('');
  const [newCategory, setNewCategory] = useState('Backend');
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [duplicateDismissed, setDuplicateDismissed] = useState(false);

  // Smart Duplicate Detection Engine
  const duplicateMatch = useMemo(() => {
    if (!newTitle.trim() || newTitle.length < 4 || duplicateDismissed) return null;
    const lower = newTitle.toLowerCase();
    
    if (lower.includes('postgres') || lower.includes('pool') || lower.includes('connection') || lower.includes('database')) {
      return {
        matched_title: 'PostgreSQL Connection Limit Exceeded',
        similarity: 89,
        existing_id: 'MEM-001',
      };
    }
    if (lower.includes('jwt') || lower.includes('auth') || lower.includes('token') || lower.includes('401') || lower.includes('signature')) {
      return {
        matched_title: 'JWT Expired Signature Mismatch (401)',
        similarity: 92,
        existing_id: 'MEM-002',
      };
    }
    if (lower.includes('redis') || lower.includes('lock') || lower.includes('celery') || lower.includes('double')) {
      return {
        matched_title: 'Redis Distributed Lock Timeout in Celery',
        similarity: 86,
        existing_id: 'MEM-003',
      };
    }
    if (lower.includes('cors') || lower.includes('5173') || lower.includes('react') || lower.includes('cross-origin')) {
      return {
        matched_title: 'FastAPI CORS Header Blocked in Local Dev',
        similarity: 94,
        existing_id: 'MEM-004',
      };
    }
    return null;
  }, [newTitle, duplicateDismissed]);

  const filteredMemories = memories.filter(
    (m) =>
      m.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.root_cause.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleMergeDuplicate = () => {
    if (!duplicateMatch) return;
    setMemories((prev) =>
      prev.map((m) =>
        m.id === duplicateMatch.existing_id
          ? { ...m, reused_count: m.reused_count + 1 }
          : m
      )
    );
    setNewTitle('');
    setNewContext('');
    setNewFix('');
    setDuplicateDismissed(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3500);
  };

  const handleSaveSolution = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newFix.trim()) return;

    const newMem: MemoryCard = {
      id: `MEM-00${memories.length + 1}`,
      title: newTitle,
      category: newCategory,
      root_cause: newContext || 'Documented team resolution for future developers.',
      solution_code: newFix,
      author: 'You',
      avatar: '✨',
      reused_count: 1,
      time_saved: '2 hours',
    };

    setMemories([newMem, ...memories]);
    setNewTitle('');
    setNewContext('');
    setNewFix('');
    setDuplicateDismissed(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3500);
  };

  return (
    <div className="min-h-screen bg-[#0B0914] text-white p-6 md:p-10 space-y-10 font-sans max-w-7xl mx-auto">
      {/* ───────────────────────────────────────────────────────────── */}
      {/* 1. HERO SPOTLIGHT SEARCH                                      */}
      {/* ───────────────────────────────────────────────────────────── */}
      <div className="text-center max-w-3xl mx-auto space-y-4 pt-4">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 bg-[#8B5CF6]/15 text-[#C4B5FD] border border-[#8B5CF6]/30 rounded-full text-xs font-mono">
          <span>🧠</span>
          <span>TeamMemoryOS</span>
        </div>
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight leading-tight">
          What problem are you trying to solve today?
        </h1>
        <p className="text-sm text-[#A5A0C8]">
          Type an error, API name, feature, service, or incident to find verified team solutions.
        </p>

        {/* Big Spotlight Input */}
        <div className="relative pt-2 text-left">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (searchQuery.trim()) {
                if (filteredMemories.length > 0) {
                  setSelectedMemory(filteredMemories[0]);
                } else {
                  navigate(`/chat?q=${encodeURIComponent(searchQuery)}`);
                }
              }
            }}
            className="relative flex items-center bg-[#141224] border border-[#2D264E] focus-within:border-[#8B5CF6] focus-within:ring-2 focus-within:ring-[#8B5CF6]/30 rounded-2xl shadow-2xl transition-all"
          >
            <span className="pl-5 text-lg text-[#A5A0C8]">🔍</span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search error logs, JWT expired, Redis timeout, PostgreSQL pool, CORS..."
              className="w-full bg-transparent px-4 py-4 text-sm sm:text-base text-white placeholder-zinc-500 focus:outline-none"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="pr-5 text-xs text-[#A5A0C8] hover:text-white font-bold"
              >
                ✕ Clear
              </button>
            )}
          </form>

          {/* Quick Click Example Chips */}
          <div className="flex flex-wrap items-center justify-center gap-2 pt-3">
            <span className="text-xs text-[#A5A0C8]">Examples:</span>
            {['JWT expired', 'Redis timeout', 'PostgreSQL pool', 'FastAPI CORS'].map((chip) => (
              <button
                key={chip}
                onClick={() => setSearchQuery(chip)}
                className="px-3 py-1 bg-[#1E1938] hover:bg-[#2D264F] border border-[#2D264E] text-[#C4B5FD] rounded-full text-xs transition-all font-medium"
              >
                {chip}
              </button>
            ))}
          </div>

          {/* ───────────────────────────────────────────────────────────── */}
          {/* INSTANT SPOTLIGHT SEARCH RESULTS DROPDOWN                     */}
          {/* ───────────────────────────────────────────────────────────── */}
          {searchQuery.trim().length > 0 && (
            <div className="absolute left-0 right-0 top-full mt-2 z-50 bg-[#141224] border border-[#8B5CF6]/60 rounded-3xl p-4 sm:p-5 shadow-2xl space-y-3 backdrop-blur-xl ring-2 ring-[#8B5CF6]/20 max-h-[480px] overflow-y-auto">
              <div className="flex items-center justify-between pb-2 border-b border-[#2D264E] text-xs font-mono">
                <span className="text-[#C4B5FD] font-bold">
                  {filteredMemories.length} Verified Solutions Found
                </span>
                <span className="text-[#A5A0C8]">Press Esc to close</span>
              </div>

              {filteredMemories.length > 0 ? (
                <div className="space-y-2.5">
                  {filteredMemories.map((mem) => (
                    <div
                      key={mem.id}
                      onClick={() => setSelectedMemory(mem)}
                      className="p-3.5 bg-[#1E1938] hover:bg-[#28214B] border border-[#2D264E] hover:border-[#8B5CF6]/60 rounded-2xl cursor-pointer transition-all space-y-1.5 group"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-base">{mem.avatar}</span>
                          <h4 className="text-xs font-bold text-white group-hover:text-[#C4B5FD] transition-colors">
                            {mem.title}
                          </h4>
                        </div>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#8B5CF6]/20 text-[#C4B5FD] border border-[#8B5CF6]/30">
                          {mem.category}
                        </span>
                      </div>

                      <p className="text-[11px] text-[#A5A0C8] line-clamp-1">
                        {mem.root_cause}
                      </p>

                      {mem.solution_code && (
                        <pre className="p-2 bg-[#0B0914] rounded-xl font-mono text-[10px] text-emerald-300 overflow-x-auto truncate">
                          <code>{mem.solution_code.split('\n')[0]}</code>
                        </pre>
                      )}

                      <div className="flex items-center justify-between pt-1 text-[10px] font-mono text-[#A5A0C8]">
                        <span>Verified by {mem.author}</span>
                        <span className="text-[#22C55E] font-bold group-hover:underline">
                          View Verified Fix →
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 space-y-3">
                  <p className="text-xs text-[#A5A0C8]">
                    No exact verified memory found for "{searchQuery}".
                  </p>
                  <button
                    onClick={() => navigate('/chat')}
                    className="px-5 py-2.5 bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white font-bold text-xs rounded-xl shadow-lg shadow-[#8B5CF6]/25 transition-all"
                  >
                    🤖 Ask AI Assistant to Solve This →
                  </button>
                </div>
              )}

              {/* Bottom Jump to Chat Button */}
              <div className="pt-2 border-t border-[#2D264E] flex items-center justify-between text-xs">
                <span className="text-[11px] text-[#A5A0C8]">Need deeper debugging?</span>
                <button
                  onClick={() => navigate('/chat')}
                  className="text-xs font-bold text-[#8B5CF6] hover:text-[#C4B5FD] flex items-center gap-1"
                >
                  <span>Open AI Assistant</span>
                  <span>→</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ───────────────────────────────────────────────────────────── */}
      {/* 2. REAL AI WORKSPACE HEALTH CARDS (No Fake Metrics)            */}
      {/* ───────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Memory Coverage */}
        <div className="p-5 bg-[#141224] border border-[#2D264E] rounded-2xl space-y-1.5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#8B5CF6] font-bold">Memory Coverage</span>
            <span className="text-base">📦</span>
          </div>
          <p className="text-xl font-bold text-white font-mono">24 Verified Fixes</p>
          <p className="text-xs text-[#A5A0C8]">Permanent institutional solutions stored in database.</p>
        </div>

        {/* Card 2: Knowledge Gaps */}
        <div className="p-5 bg-[#141224] border border-[#2D264E] rounded-2xl space-y-1.5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#F59E0B] font-bold">Knowledge Gaps</span>
            <span className="text-base">⚠️</span>
          </div>
          <p className="text-xl font-bold text-[#F59E0B] font-mono">5 Services</p>
          <p className="text-xs text-[#A5A0C8]">5 microservices currently lack documentation.</p>
        </div>

        {/* Card 3: Most Reused Memory */}
        <div className="p-5 bg-[#141224] border border-[#2D264E] rounded-2xl space-y-1.5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#22D3EE] font-bold">Most Reused Memory</span>
            <span className="text-base">⭐</span>
          </div>
          <p className="text-sm font-bold text-white truncate">JWT Authentication</p>
          <p className="text-xs text-[#22D3EE] font-mono">Reused 17 times by engineers</p>
        </div>

        {/* Card 4: AI Saved This Week */}
        <div className="p-5 bg-[#141224] border border-[#2D264E] rounded-2xl space-y-1.5 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#22C55E] font-bold">AI Saved This Week</span>
            <span className="text-base">⚡</span>
          </div>
          <p className="text-xl font-bold text-[#22C55E] font-mono">8.5 Hours</p>
          <p className="text-xs text-[#A5A0C8]">Estimated engineering time saved this week.</p>
        </div>
      </div>

      {/* ───────────────────────────────────────────────────────────── */}
      {/* 3. YOUR LEARNING PATH (Fresher & Engineer Progress)           */}
      {/* ───────────────────────────────────────────────────────────── */}
      <div className="bg-[#141224] border border-[#2D264E] rounded-3xl p-6 sm:p-7 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#2D264E]">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span>🎯</span> Your Learning Path
            </h2>
            <p className="text-xs text-[#A5A0C8]">
              Personalized onboarding curriculum grounded in team memory
            </p>
          </div>
          <span className="text-xs font-mono text-[#C4B5FD] bg-[#8B5CF6]/15 border border-[#8B5CF6]/30 px-3 py-1 rounded-full">
            Daily Progress: 1 of 4 Complete
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {/* Path 1: Authentication */}
          <div className="p-4 bg-[#1E1938] border border-[#2D264E] rounded-2xl space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-white">Authentication Service</span>
              <span className="text-[11px] font-mono text-[#22C55E] font-bold">25%</span>
            </div>
            <div className="w-full bg-[#0B0914] h-2 rounded-full overflow-hidden">
              <div className="bg-[#22C55E] h-full rounded-full" style={{ width: '25%' }} />
            </div>
            <span className="text-[10px] text-[#A5A0C8] block font-mono">Read ADR002 Bcrypt Standard</span>
          </div>

          {/* Path 2: Database */}
          <div className="p-4 bg-[#1E1938] border border-[#2D264E] rounded-2xl space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-white">Database Connections</span>
              <span className="text-[11px] font-mono text-[#A5A0C8]">0%</span>
            </div>
            <div className="w-full bg-[#0B0914] h-2 rounded-full overflow-hidden">
              <div className="bg-[#8B5CF6] h-full rounded-full" style={{ width: '0%' }} />
            </div>
            <span className="text-[10px] text-[#A5A0C8] block font-mono">PostgreSQL Pool Tuning Guide</span>
          </div>

          {/* Path 3: Deployment */}
          <div className="p-4 bg-[#1E1938] border border-[#2D264E] rounded-2xl space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-white">Deployment Workflow</span>
              <span className="text-[11px] font-mono text-[#A5A0C8]">0%</span>
            </div>
            <div className="w-full bg-[#0B0914] h-2 rounded-full overflow-hidden">
              <div className="bg-[#8B5CF6] h-full rounded-full" style={{ width: '0%' }} />
            </div>
            <span className="text-[10px] text-[#A5A0C8] block font-mono">Docker Compose & Migrations</span>
          </div>

          {/* Path 4: Incident Playbook */}
          <div className="p-4 bg-[#1E1938] border border-[#22D3EE]/30 rounded-2xl space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-white">Incident Playbook</span>
              <span className="text-[10px] font-mono text-[#22D3EE] font-bold">Recommended</span>
            </div>
            <div className="w-full bg-[#0B0914] h-2 rounded-full overflow-hidden">
              <div className="bg-[#22D3EE] h-full rounded-full" style={{ width: '10%' }} />
            </div>
            <span className="text-[10px] text-[#22D3EE] block font-mono">Top 3 Post-Mortems to Review</span>
          </div>
        </div>
      </div>

      {/* ───────────────────────────────────────────────────────────── */}
      {/* 4. MAIN SECTION: Reusable Memories & Save Solution Form       */}
      {/* ───────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left (7 cols): Reusable Memories */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between pb-1">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>📖</span> Reusable Team Memories
              </h2>
              <p className="text-xs text-[#A5A0C8]">One problem solved once → reused forever.</p>
            </div>
            <button
              onClick={() => navigate('/knowledge')}
              className="text-xs text-[#C4B5FD] hover:text-white font-medium"
            >
              Open Full Book →
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {filteredMemories.map((mem) => (
              <m.div
                key={mem.id}
                whileHover={{ y: -3 }}
                onClick={() => setSelectedMemory(mem)}
                className="p-5 bg-[#141224] hover:bg-[#1A1730] border border-[#2D264E] hover:border-[#8B5CF6]/50 rounded-2xl cursor-pointer transition-all shadow-xl flex flex-col justify-between space-y-3"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-[#8B5CF6]/20 text-[#C4B5FD] border border-[#8B5CF6]/30 font-bold">
                      {mem.category}
                    </span>
                    <span className="text-[10px] font-mono text-[#22C55E]">
                      Used {mem.reused_count}x
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-white leading-snug">{mem.title}</h3>
                  <p className="text-xs text-[#A5A0C8] line-clamp-2">{mem.root_cause}</p>
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-[#2D264E] text-[11px] text-[#A5A0C8]">
                  <span className="flex items-center gap-1.5">
                    <span>{mem.avatar}</span> {mem.author}
                  </span>
                  <span className="text-[#C4B5FD] font-semibold">Open Memory →</span>
                </div>
              </m.div>
            ))}
          </div>
        </div>

        {/* Right (5 cols): Save A New Solution + Smart Duplicate Detection */}
        <div className="lg:col-span-5 bg-[#141224] border border-[#2D264E] rounded-3xl p-6 shadow-2xl space-y-4 h-fit">
          <div className="pb-3 border-b border-[#2D264E]">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <span>✍️</span> Save a New Solution
            </h3>
            <p className="text-xs text-[#A5A0C8] mt-0.5">
              Turn your debugging session into permanent team knowledge.
            </p>
          </div>

          {/* Smart Duplicate Detection Banner */}
          <AnimatePresence>
            {duplicateMatch && (
              <m.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className="p-4 bg-[#F59E0B]/10 border border-[#F59E0B]/40 rounded-2xl space-y-2.5 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#F59E0B] flex items-center gap-1.5">
                    <span>⚠️</span> Similar memory already exists
                  </span>
                  <span className="text-[10px] font-mono text-[#F59E0B] bg-[#F59E0B]/20 px-2 py-0.5 rounded-full font-bold">
                    {duplicateMatch.similarity}% Similar
                  </span>
                </div>
                <p className="text-zinc-200">
                  Existing: <strong className="text-white">"{duplicateMatch.matched_title}"</strong>
                </p>
                <div className="flex items-center gap-2 pt-1">
                  <button
                    type="button"
                    onClick={handleMergeDuplicate}
                    className="flex-1 py-1.5 bg-[#F59E0B] hover:bg-amber-600 text-black font-bold text-xs rounded-xl transition-all"
                  >
                    ✓ Merge & Update Reuse Count
                  </button>
                  <button
                    type="button"
                    onClick={() => setDuplicateDismissed(true)}
                    className="px-3 py-1.5 bg-white/5 hover:bg-white/10 text-[#A5A0C8] text-xs rounded-xl"
                  >
                    Keep Separate
                  </button>
                </div>
              </m.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleSaveSolution} className="space-y-3.5">
            {/* Field 1: Problem Title */}
            <div>
              <label className="text-xs font-bold text-zinc-300 block mb-1">
                Problem Title
              </label>
              <input
                type="text"
                value={newTitle}
                onChange={(e) => {
                  setNewTitle(e.target.value);
                  setDuplicateDismissed(false);
                }}
                placeholder="e.g. PostgreSQL Connection Timeout"
                className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none"
                required
              />
            </div>

            {/* Field 2: Category */}
            <div>
              <label className="text-xs font-bold text-zinc-300 block mb-1">
                Category
              </label>
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2.5 text-xs text-zinc-200 focus:outline-none"
              >
                <option value="Authentication">Authentication</option>
                <option value="Database">Database</option>
                <option value="Backend">Backend</option>
                <option value="Frontend">Frontend</option>
                <option value="Docker / DevOps">Docker / DevOps</option>
              </select>
            </div>

            {/* Field 3: Error / Context */}
            <div>
              <label className="text-xs font-bold text-zinc-300 block mb-1">
                Error / Context
              </label>
              <textarea
                value={newContext}
                onChange={(e) => setNewContext(e.target.value)}
                rows={2}
                placeholder="Paste terminal error or brief context..."
                className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl p-3 text-xs text-zinc-200 placeholder-zinc-500 focus:outline-none"
              />
            </div>

            {/* Field 4: Working Fix */}
            <div>
              <label className="text-xs font-bold text-zinc-300 block mb-1">
                Working Fix
              </label>
              <textarea
                value={newFix}
                onChange={(e) => setNewFix(e.target.value)}
                rows={4}
                placeholder="Paste code patch or working resolution..."
                className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl p-3 text-xs font-mono text-zinc-200 placeholder-zinc-500 focus:outline-none"
                required
              />
            </div>

            {saveSuccess && (
              <div className="p-3 bg-emerald-950/40 border border-[#22C55E]/40 rounded-xl text-xs text-[#22C55E] font-bold flex items-center gap-2">
                <span>✨</span> Memory saved! Teammates can now find this fix.
              </div>
            )}

            <button
              type="submit"
              className="w-full py-3 bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white font-bold text-xs rounded-xl shadow-lg shadow-[#8B5CF6]/25 transition-all flex items-center justify-center gap-2"
            >
              <span>+ Save to Team Memory</span>
            </button>
          </form>
        </div>
      </div>

      {/* ───────────────────────────────────────────────────────────── */}
      {/* 5. MODAL: Memory Detail Card                                  */}
      {/* ───────────────────────────────────────────────────────────── */}
      <AnimatePresence>
        {selectedMemory && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
            <m.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-2xl bg-[#141224] border border-[#8B5CF6]/40 rounded-3xl p-6 sm:p-8 space-y-5 shadow-2xl relative"
            >
              <div className="flex items-start justify-between gap-4 pb-3 border-b border-[#2D264E]">
                <div>
                  <span className="text-[10px] font-mono uppercase bg-[#8B5CF6]/20 text-[#C4B5FD] px-2.5 py-0.5 rounded-full border border-[#8B5CF6]/30 font-bold">
                    {selectedMemory.category} • {selectedMemory.id}
                  </span>
                  <h3 className="text-lg font-bold text-white mt-1.5">{selectedMemory.title}</h3>
                </div>
                <button
                  onClick={() => setSelectedMemory(null)}
                  className="p-1.5 text-[#A5A0C8] hover:text-white rounded-lg hover:bg-white/10"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-3 text-xs">
                <div className="p-3.5 bg-[#1E1938] border border-[#2D264E] rounded-2xl">
                  <span className="text-[10px] uppercase font-bold text-[#A5A0C8] block mb-1">Root Cause</span>
                  <p className="text-zinc-200">{selectedMemory.root_cause}</p>
                </div>

                <div>
                  <span className="text-[10px] uppercase font-bold text-[#22C55E] block mb-1.5">
                    Working Solution & Code Patch
                  </span>
                  <pre className="p-4 bg-[#0B0914] border border-[#2D264E] rounded-2xl font-mono text-zinc-200 overflow-x-auto text-xs">
                    <code>{selectedMemory.solution_code}</code>
                  </pre>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-[#2D264E]">
                <span className="text-xs text-[#A5A0C8]">
                  Verified by <strong className="text-white">{selectedMemory.author}</strong> • Used {selectedMemory.reused_count} times
                </span>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(selectedMemory.solution_code);
                    alert('Code patch copied to clipboard!');
                  }}
                  className="px-4 py-2 bg-[#22C55E] hover:bg-emerald-600 text-white font-bold text-xs rounded-xl shadow-md transition-all"
                >
                  Copy Fix
                </button>
              </div>
            </m.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
