import { useState } from 'react';
import { m, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@stores/authStore';

interface MemoryItem {
  id: string;
  title: string;
  category: string;
  problem: string;
  symptoms: string;
  root_cause: string;
  working_solution: string;
  code_patch: string;
  verified_by: string;
  avatar: string;
  times_reused: number;
  date: string;
  related_services: string[];
  related_memories: string[];
}

const MEMORY_CATALOG: MemoryItem[] = [
  {
    id: 'MEM-001',
    title: 'PostgreSQL Connection Limit Exceeded (Pool Exhaustion)',
    category: 'Database',
    problem: 'Database connection pool reached maximum size under concurrent async background worker tasks.',
    symptoms: 'QueuePool limit of size 10 overflow 10 reached, connection timed out, timeout 30.00',
    root_cause: 'Unclosed cursor sessions and default pool_size=10 exhausted by concurrent Celery workers.',
    working_solution: 'Configure SQLAlchemy create_engine with pool_size=50, max_overflow=20, and pool_pre_ping=True.',
    code_patch: `engine = create_engine(
    DATABASE_URL,
    pool_size=50,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)`,
    verified_by: 'Sarah Connor',
    avatar: 'SC',
    times_reused: 24,
    date: 'Yesterday',
    related_services: ['PostgreSQL Database', 'Async Worker Queue', 'API Gateway'],
    related_memories: ['ADR001: Database Architecture', 'INC012: Pool Starvation'],
  },
  {
    id: 'MEM-002',
    title: 'JWT Bearer Authentication Signature Mismatch (401 Unauthorized)',
    category: 'Authentication',
    problem: 'Protected API endpoints returning 401 Unauthorized during token validation.',
    symptoms: 'jwt.exceptions.InvalidSignatureError: Signature verification failed for token',
    root_cause: 'Missing algorithm="HS256" and token clock skew tolerance in auth middleware after secret rotation.',
    working_solution: 'Enforce explicit algorithms=["HS256"] in jwt.decode with 30-second clock skew tolerance.',
    code_patch: `def verify_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"leeway": 30})`,
    verified_by: 'Devin Thorne',
    avatar: 'DT',
    times_reused: 28,
    date: '3 days ago',
    related_services: ['Auth Service', 'User Service', 'API Gateway'],
    related_memories: ['ADR002: Password & JWT Security', 'INC008: Auth Token Leak'],
  },
  {
    id: 'MEM-003',
    title: 'Redis Distributed Redlock Timeout in Celery Queue',
    category: 'Backend',
    problem: 'Duplicate webhook executions causing double charge invoice settlements.',
    symptoms: 'IntegrityError: duplicate key value violates unique constraint "invoices_pkey"',
    root_cause: 'Concurrent payment callbacks processed simultaneously without distributed lock synchronization.',
    working_solution: 'Wrap checkout and payment handlers with atomic Redis distributed lock.',
    code_patch: `with redis_client.lock("checkout_lock", timeout=15):
    process_payment(order_id)`,
    verified_by: 'Alex Vance',
    avatar: 'AV',
    times_reused: 19,
    date: '5 days ago',
    related_services: ['Billing Service', 'Redis Cache', 'Worker Queue'],
    related_memories: ['ADR003: Redis Locking Standard', 'INC007: Webhook Race Condition'],
  },
  {
    id: 'MEM-004',
    title: 'FastAPI CORS Header Blocked in Local Frontend Dev',
    category: 'Frontend',
    problem: 'Vite React frontend on localhost:5173 unable to call backend API routes due to browser CORS blocking.',
    symptoms: 'Access to XMLHttpRequest at http://localhost:8000 from origin http://localhost:5173 has been blocked by CORS policy',
    root_cause: 'FastAPI application lacked CORSMiddleware configuration for localhost:5173 origins.',
    working_solution: 'Add CORSMiddleware in FastAPI main application with localhost:5173 allowed origin.',
    code_patch: `app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)`,
    verified_by: 'Devin Thorne',
    avatar: 'DT',
    times_reused: 35,
    date: '1 week ago',
    related_services: ['Frontend React App', 'Backend FastAPI'],
    related_memories: ['MEM-005: Local Dev Environment'],
  },
  {
    id: 'MEM-005',
    title: 'SQLAlchemy 2.0 Select Statement Migration & Parameterization',
    category: 'Database',
    problem: 'Legacy db.session.query() statements causing deprecation warnings in SQLAlchemy 2.0.',
    symptoms: 'RemovedIn20Warning: The Query.get() method is considered legacy as of the 1.x series',
    root_cause: 'SQLAlchemy 2.0 transition requires modern select() and session.scalars() paradigm.',
    working_solution: 'Migrate to select(Model).where() with session.scalars(stmt).first().',
    code_patch: `stmt = select(User).where(User.email == email)
user = db.scalars(stmt).first()`,
    verified_by: 'Sarah Connor',
    avatar: 'SC',
    times_reused: 15,
    date: '2 weeks ago',
    related_services: ['PostgreSQL Database', 'User Service'],
    related_memories: ['ADR001: SQL Parameterization Standard', 'POL-01: Zero SQL Injections'],
  },
];

const CATEGORIES = ['ALL', 'Database', 'Authentication', 'Backend', 'Frontend', 'Docker', 'Security'];

export function KnowledgePage() {
  const user = useAuthStore((s) => s.user);

  const [memories, setMemories] = useState<MemoryItem[]>(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('teammemory_saved_memories') || '[]');
      if (Array.isArray(saved) && saved.length > 0) {
        return [...saved, ...MEMORY_CATALOG];
      }
    } catch (e) {
      // pass
    }
    return MEMORY_CATALOG;
  });

  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'gallery' | 'timeline' | 'list'>('gallery');
  const [activeMemory, setActiveMemory] = useState<MemoryItem | null>(null);

  // Add Memory Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newCategory, setNewCategory] = useState('Backend');
  const [newProblem, setNewProblem] = useState('');
  const [newSolution, setNewSolution] = useState('');
  const [newCodePatch, setNewCodePatch] = useState('');
  const [newServices, setNewServices] = useState('Core Backend API, PostgreSQL');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const handleCreateMemory = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newSolution.trim()) return;

    const authorName = user?.full_name || 'Engineering Team';
    const authorInitials = authorName.replace(/[^a-zA-Z]/g, '').slice(0, 2).toUpperCase() || 'EN';

    const newMem: MemoryItem = {
      id: `MEM-00${memories.length + 1}`,
      title: newTitle.trim(),
      category: newCategory,
      problem: newProblem.trim() || 'Documented team resolution.',
      symptoms: newProblem.trim().slice(0, 80),
      root_cause: newProblem.trim() || 'Applied engineering architectural standard.',
      working_solution: newSolution.trim(),
      code_patch: newCodePatch.trim(),
      verified_by: authorName,
      avatar: authorInitials,
      times_reused: 1,
      date: 'Just now',
      related_services: newServices.split(',').map((s) => s.trim()).filter(Boolean),
      related_memories: ['Verified Team Resolution'],
    };

    const updated = [newMem, ...memories];
    setMemories(updated);
    try {
      localStorage.setItem('teammemory_saved_memories', JSON.stringify(updated));
    } catch (e) {}

    // Reset Form
    setNewTitle('');
    setNewProblem('');
    setNewSolution('');
    setNewCodePatch('');
    setShowCreateModal(false);

    setToastMessage(`✓ "${newMem.title}" successfully added to Memory Book`);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const filteredMemories = memories.filter((m) => {
    const matchesCat = selectedCategory === 'ALL' || m.category.toLowerCase() === selectedCategory.toLowerCase();
    const matchesSearch =
      m.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.problem.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="min-h-screen bg-[#0B0914] text-white p-6 md:p-10 space-y-8 font-sans max-w-7xl mx-auto">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-6 right-6 z-50 px-4 py-3 bg-[#22C55E]/15 border border-[#22C55E]/40 text-[#22C55E] rounded-2xl text-xs font-mono shadow-2xl backdrop-blur-md animate-fade-in flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-[#22C55E]" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header & View Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#2D264E]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono text-[#A5A0C8] uppercase tracking-wider">
              Institutional Knowledge Library
            </span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#8B5CF6]/15 text-[#C4B5FD] border border-[#8B5CF6]/30 font-medium">
              Verified Solutions
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Memory Book
          </h1>
          <p className="text-xs text-[#A5A0C8] mt-0.5">
            Every engineering problem solved once becomes reusable team knowledge for everyone.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Primary + Add Memory Button */}
          <button
            type="button"
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white font-bold text-xs rounded-xl shadow-lg shadow-[#8B5CF6]/25 transition-all flex items-center gap-1.5"
          >
            <span>+ Add Memory</span>
          </button>

          {/* View Switcher: Gallery | Timeline | List */}
          <div className="flex items-center gap-1 bg-[#141224] border border-[#2D264E] p-1 rounded-2xl text-xs shadow-xl">
            <button
              type="button"
              onClick={() => setViewMode('gallery')}
              className={`px-3 py-1.5 font-bold rounded-xl transition-all ${
                viewMode === 'gallery'
                  ? 'bg-[#8B5CF6] text-white shadow-md shadow-[#8B5CF6]/20'
                  : 'text-[#A5A0C8] hover:text-white'
              }`}
            >
              Gallery
            </button>
            <button
              type="button"
              onClick={() => setViewMode('timeline')}
              className={`px-3 py-1.5 font-bold rounded-xl transition-all ${
                viewMode === 'timeline'
                  ? 'bg-[#8B5CF6] text-white shadow-md shadow-[#8B5CF6]/20'
                  : 'text-[#A5A0C8] hover:text-white'
              }`}
            >
              Timeline
            </button>
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 font-bold rounded-xl transition-all ${
                viewMode === 'list'
                  ? 'bg-[#8B5CF6] text-white shadow-md shadow-[#8B5CF6]/20'
                  : 'text-[#A5A0C8] hover:text-white'
              }`}
            >
              List
            </button>
          </div>
        </div>
      </div>

      {/* Search & Filter Chips Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Category Chips */}
        <div className="flex flex-wrap items-center gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setSelectedCategory(cat)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all border ${
                selectedCategory === cat
                  ? 'bg-[#8B5CF6] text-white border-[#8B5CF6] shadow-md shadow-[#8B5CF6]/20'
                  : 'bg-[#141224] border-[#2D264E] text-[#A5A0C8] hover:text-white hover:border-[#8B5CF6]/40'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search Box */}
        <div className="w-full sm:w-72">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search verified fixes..."
            className="w-full bg-[#141224] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-4 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none font-mono"
          />
        </div>
      </div>

      {/* ───────────────────────────────────────────────────────────── */}
      {/* VIEW 1: Gallery View (Visual Cards)                           */}
      {/* ───────────────────────────────────────────────────────────── */}
      {viewMode === 'gallery' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredMemories.map((mem) => (
            <m.div
              key={mem.id}
              whileHover={{ y: -3 }}
              onClick={() => setActiveMemory(mem)}
              className="bg-[#141224] hover:bg-[#1A1730] border border-[#2D264E] hover:border-[#8B5CF6]/50 rounded-3xl p-6 shadow-xl cursor-pointer transition-all flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-[#8B5CF6]/20 text-[#C4B5FD] border border-[#8B5CF6]/30 font-bold">
                    {mem.category}
                  </span>
                  <span className="text-[11px] font-mono text-[#22C55E] font-bold">
                    Reused {mem.times_reused}x
                  </span>
                </div>

                <h3 className="text-sm font-bold text-white leading-snug">{mem.title}</h3>
                <p className="text-xs text-[#A5A0C8] line-clamp-2">{mem.problem}</p>
              </div>

              <div className="pt-3 border-t border-[#2D264E] flex items-center justify-between text-xs text-[#A5A0C8]">
                <span className="flex items-center gap-2 font-mono">
                  <div className="h-6 w-6 rounded-md bg-[#8B5CF6]/20 text-[#C4B5FD] flex items-center justify-center text-[10px] font-bold">
                    {mem.avatar || 'EN'}
                  </div>
                  <span>{mem.verified_by}</span>
                </span>
                <span className="text-[#C4B5FD] font-semibold text-xs">Open Solution →</span>
              </div>
            </m.div>
          ))}
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────── */}
      {/* VIEW 2: Timeline View                                         */}
      {/* ───────────────────────────────────────────────────────────── */}
      {viewMode === 'timeline' && (
        <div className="relative pl-6 sm:pl-8 border-l border-[#8B5CF6]/30 space-y-8 max-w-4xl mx-auto">
          {filteredMemories.map((mem) => (
            <div key={mem.id} className="relative group">
              <div className="absolute -left-[31px] sm:-left-[39px] top-1.5 h-4 w-4 rounded-full bg-[#8B5CF6] border-4 border-[#0B0914] shadow-md shadow-[#8B5CF6]/50" />

              <div
                onClick={() => setActiveMemory(mem)}
                className="bg-[#141224] border border-[#2D264E] hover:border-[#8B5CF6]/50 rounded-2xl p-5 shadow-lg cursor-pointer transition-all space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[#8B5CF6]/20 text-[#C4B5FD] font-bold">
                      {mem.category}
                    </span>
                    <span className="text-xs text-[#A5A0C8] font-mono">{mem.date}</span>
                  </div>
                  <span className="text-xs text-[#22C55E] font-mono">Reused {mem.times_reused} times</span>
                </div>

                <h3 className="text-sm font-bold text-white group-hover:text-[#C4B5FD] transition-colors">
                  {mem.title}
                </h3>
                <p className="text-xs text-[#A5A0C8]">{mem.problem}</p>

                {mem.code_patch && (
                  <pre className="p-3 bg-[#0B0914] border border-[#2D264E] rounded-xl font-mono text-[11px] text-[#C4B5FD] overflow-x-auto">
                    <code>{mem.code_patch.slice(0, 120)}...</code>
                  </pre>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────── */}
      {/* VIEW 3: List View                                             */}
      {/* ───────────────────────────────────────────────────────────── */}
      {viewMode === 'list' && (
        <div className="bg-[#141224] border border-[#2D264E] rounded-2xl overflow-hidden shadow-xl">
          <div className="divide-y divide-[#2D264E]">
            {filteredMemories.map((mem) => (
              <div
                key={mem.id}
                onClick={() => setActiveMemory(mem)}
                className="p-4 sm:p-5 hover:bg-[#1E1938] cursor-pointer transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-[#8B5CF6]/20 text-[#C4B5FD] font-bold">
                      {mem.category}
                    </span>
                    <h3 className="text-sm font-bold text-white">{mem.title}</h3>
                  </div>
                  <p className="text-xs text-[#A5A0C8] line-clamp-1">{mem.problem}</p>
                </div>

                <div className="flex items-center gap-4 text-xs font-mono text-[#A5A0C8] flex-shrink-0">
                  <span>Reused {mem.times_reused}x</span>
                  <span>{mem.verified_by}</span>
                  <span className="text-[#C4B5FD] font-bold">View →</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────── */}
      {/* MODAL 1: ADD NEW MEMORY MODAL                                 */}
      {/* ───────────────────────────────────────────────────────────── */}
      <AnimatePresence>
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <m.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#141224] border border-[#8B5CF6]/50 rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 sm:p-8 shadow-2xl space-y-5"
            >
              <div className="flex items-center justify-between pb-3 border-b border-[#2D264E]">
                <div>
                  <h2 className="text-lg font-bold text-white">Add Solution to Memory Book</h2>
                  <p className="text-xs text-[#A5A0C8]">
                    Save an engineering problem and verified fix as permanent team memory.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="h-8 w-8 rounded-xl bg-[#1E1938] text-[#A5A0C8] hover:text-white flex items-center justify-center text-xs"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleCreateMemory} className="space-y-4 text-left">
                <div>
                  <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                    Problem / Memory Title:
                  </label>
                  <input
                    type="text"
                    required
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="e.g. Celery Redis Timeout under High Concurrency"
                    className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                      Architecture Category:
                    </label>
                    <select
                      value={newCategory}
                      onChange={(e) => setNewCategory(e.target.value)}
                      className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none"
                    >
                      <option value="Database">Database & PostgreSQL</option>
                      <option value="Authentication">Authentication & Security</option>
                      <option value="Backend">Backend & Concurrency</option>
                      <option value="Frontend">Frontend & React</option>
                      <option value="Docker">Docker & Infrastructure</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                      Affected Services:
                    </label>
                    <input
                      type="text"
                      value={newServices}
                      onChange={(e) => setNewServices(e.target.value)}
                      placeholder="e.g. Core API, PostgreSQL DB"
                      className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                    Problem Scenario / Root Cause:
                  </label>
                  <textarea
                    rows={3}
                    value={newProblem}
                    onChange={(e) => setNewProblem(e.target.value)}
                    placeholder="Describe what went wrong, symptoms, and the underlying root cause..."
                    className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                    Verified Solution Summary:
                  </label>
                  <input
                    type="text"
                    required
                    value={newSolution}
                    onChange={(e) => setNewSolution(e.target.value)}
                    placeholder="e.g. Set pool_pre_ping=True and increase max_overflow in create_engine"
                    className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                    Solution Code Snippet / Patch (Optional):
                  </label>
                  <textarea
                    rows={4}
                    value={newCodePatch}
                    onChange={(e) => setNewCodePatch(e.target.value)}
                    placeholder="# Paste the working code snippet..."
                    className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl p-3 font-mono text-xs text-[#C4B5FD] placeholder-zinc-600 focus:outline-none"
                  />
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2.5 bg-[#1E1938] hover:bg-[#28214B] border border-[#2D264E] text-[#A5A0C8] rounded-xl text-xs font-semibold transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-6 py-2.5 bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white font-bold text-xs rounded-xl shadow-lg shadow-[#8B5CF6]/25 transition-all"
                  >
                    Save Memory →
                  </button>
                </div>
              </form>
            </m.div>
          </div>
        )}
      </AnimatePresence>

      {/* ───────────────────────────────────────────────────────────── */}
      {/* MODAL 2: VIEW MEMORY DETAILS                                  */}
      {/* ───────────────────────────────────────────────────────────── */}
      <AnimatePresence>
        {activeMemory && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <m.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#141224] border border-[#8B5CF6]/50 rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 sm:p-8 shadow-2xl space-y-6"
            >
              <div className="flex items-center justify-between pb-3 border-b border-[#2D264E]">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-[#8B5CF6]/20 text-[#C4B5FD] font-bold">
                    {activeMemory.category}
                  </span>
                  <span className="text-xs text-[#22C55E] font-mono">
                    Reused {activeMemory.times_reused} times
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveMemory(null)}
                  className="h-8 w-8 rounded-xl bg-[#1E1938] text-[#A5A0C8] hover:text-white flex items-center justify-center text-xs"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4 text-left">
                <h2 className="text-xl font-bold text-white">{activeMemory.title}</h2>

                <div className="p-4 bg-[#1E1938] border border-[#2D264E] rounded-2xl space-y-2">
                  <span className="text-[10px] font-mono uppercase text-[#A5A0C8] font-bold block">
                    Problem & Root Cause:
                  </span>
                  <p className="text-xs text-white leading-relaxed">{activeMemory.problem}</p>
                </div>

                <div className="p-4 bg-[#1E1938] border border-[#22C55E]/30 rounded-2xl space-y-2">
                  <span className="text-[10px] font-mono uppercase text-[#22C55E] font-bold block">
                    Verified Solution:
                  </span>
                  <p className="text-xs text-white leading-relaxed">{activeMemory.working_solution}</p>
                </div>

                {activeMemory.code_patch && (
                  <div className="space-y-1.5">
                    <span className="text-[10px] font-mono uppercase text-[#A5A0C8] font-bold block">
                      Code Patch:
                    </span>
                    <pre className="p-4 bg-[#0B0914] border border-[#2D264E] rounded-2xl font-mono text-xs text-[#C4B5FD] overflow-x-auto shadow-inner">
                      <code>{activeMemory.code_patch}</code>
                    </pre>
                  </div>
                )}

                <div className="pt-2 flex items-center justify-between text-xs font-mono text-[#A5A0C8] border-t border-[#2D264E]">
                  <span>Verified by: <strong className="text-white">{activeMemory.verified_by}</strong></span>
                  <span>{activeMemory.date}</span>
                </div>
              </div>
            </m.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default KnowledgePage;
