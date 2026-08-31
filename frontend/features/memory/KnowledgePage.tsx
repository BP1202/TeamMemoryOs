import { useState } from 'react';
import { m, AnimatePresence } from 'framer-motion';

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
    verified_by: 'Sarah (Tech Lead)',
    avatar: '🎯',
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
    verified_by: 'Devin (Developer)',
    avatar: '💻',
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
    verified_by: 'Alex (Owner)',
    avatar: '👑',
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
    verified_by: 'Devin (Developer)',
    avatar: '💻',
    times_reused: 35,
    date: '1 week ago',
    related_services: ['Frontend React App', 'Backend FastAPI'],
    related_memories: ['MEM-005: Local Dev Environment'],
  },
  {
    id: 'MEM-005',
    title: 'Docker Container Out of Memory During Build',
    category: 'Docker',
    problem: 'Docker build process failing during Python wheels compilation on dev workstations.',
    symptoms: 'The command /bin/sh -c pip install returned a non-zero code: 137 (OOM killed)',
    root_cause: 'Container memory limit set below 1GB during heavy C-extension compilation.',
    working_solution: 'Add resource limits and memory reservations in docker-compose specification.',
    code_patch: `services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2048M`,
    verified_by: 'Morgan (Auditor)',
    avatar: '🛡️',
    times_reused: 12,
    date: '2 weeks ago',
    related_services: ['Docker Compose', 'CI/CD Pipeline'],
    related_memories: ['DEV-004: Docker Infrastructure'],
  },
  {
    id: 'MEM-006',
    title: 'Raw SQL Injection Pattern Blocked by Security Policy',
    category: 'Security',
    problem: 'Developer attempted to build dynamic query using Python f-strings without parameter binding.',
    symptoms: 'Policy violation detected: Raw string interpolation in database query execution',
    root_cause: 'Direct variable interpolation into SQL statements bypassed parameter escaping.',
    working_solution: 'Use SQLAlchemy 2.0 ORM query syntax with bound parameters.',
    code_patch: `stmt = select(User).where(User.email == email)
user = db.scalars(stmt).first()`,
    verified_by: 'Sarah (Tech Lead)',
    avatar: '🎯',
    times_reused: 15,
    date: '2 weeks ago',
    related_services: ['PostgreSQL Database', 'User Service'],
    related_memories: ['ADR001: SQL Parameterization Standard', 'POL-01: Zero SQL Injections'],
  },
];

const CATEGORIES = ['ALL', 'Database', 'Authentication', 'Backend', 'Frontend', 'Docker', 'Security'];

export function KnowledgePage() {
  const [memories] = useState<MemoryItem[]>(() => {
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
      {/* Header & View Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#2D264E]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono text-[#A5A0C8] uppercase tracking-wider">
              Institutional Knowledge Library
            </span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#8B5CF6]/15 text-[#C4B5FD] border border-[#8B5CF6]/30 font-medium">
              Notion-Grade
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <span>📖</span> Memory Book
          </h1>
          <p className="text-xs text-[#A5A0C8] mt-0.5">
            Every engineering problem solved once becomes reusable team knowledge for everyone.
          </p>
        </div>

        {/* View Switcher: Gallery | Timeline | List */}
        <div className="flex items-center gap-1 bg-[#141224] border border-[#2D264E] p-1 rounded-2xl text-xs shadow-xl">
          <button
            onClick={() => setViewMode('gallery')}
            className={`px-3 py-1.5 font-bold rounded-xl transition-all ${
              viewMode === 'gallery'
                ? 'bg-[#8B5CF6] text-white shadow-md shadow-[#8B5CF6]/20'
                : 'text-[#A5A0C8] hover:text-white'
            }`}
          >
            🖼️ Gallery
          </button>
          <button
            onClick={() => setViewMode('timeline')}
            className={`px-3 py-1.5 font-bold rounded-xl transition-all ${
              viewMode === 'timeline'
                ? 'bg-[#8B5CF6] text-white shadow-md shadow-[#8B5CF6]/20'
                : 'text-[#A5A0C8] hover:text-white'
            }`}
          >
            ⏱️ Timeline
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-1.5 font-bold rounded-xl transition-all ${
              viewMode === 'list'
                ? 'bg-[#8B5CF6] text-white shadow-md shadow-[#8B5CF6]/20'
                : 'text-[#A5A0C8] hover:text-white'
            }`}
          >
            📋 List
          </button>
        </div>
      </div>

      {/* Search & Filter Chips Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Category Chips */}
        <div className="flex flex-wrap items-center gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
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
            className="w-full bg-[#141224] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-4 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none"
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
                <span className="flex items-center gap-1.5">
                  <span>{mem.avatar}</span> {mem.verified_by}
                </span>
                <span className="text-[#C4B5FD] font-semibold">Open Solution →</span>
              </div>
            </m.div>
          ))}
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────── */}
      {/* VIEW 2: Timeline View (Chronological Engineering History)     */}
      {/* ───────────────────────────────────────────────────────────── */}
      {viewMode === 'timeline' && (
        <div className="relative pl-6 sm:pl-8 border-l border-[#8B5CF6]/30 space-y-8 max-w-4xl mx-auto">
          {filteredMemories.map((mem) => (
            <div key={mem.id} className="relative group">
              {/* Dot */}
              <div className="absolute -left-[31px] sm:-left-[39px] top-1.5 h-4 w-4 rounded-full bg-[#8B5CF6] border-4 border-[#0B0914] shadow-lg shadow-[#8B5CF6]/50" />

              <div
                onClick={() => setActiveMemory(mem)}
                className="bg-[#141224] hover:bg-[#1A1730] border border-[#2D264E] hover:border-[#8B5CF6]/50 rounded-3xl p-6 shadow-xl cursor-pointer transition-all space-y-3"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-[#8B5CF6]/20 text-[#C4B5FD] border border-[#8B5CF6]/30 font-bold">
                    {mem.category} • {mem.id}
                  </span>
                  <span className="text-[#A5A0C8] font-mono">{mem.date}</span>
                </div>

                <h3 className="text-base font-bold text-white">{mem.title}</h3>
                <p className="text-xs text-[#A5A0C8]">{mem.problem}</p>

                <div className="flex items-center justify-between pt-2 border-t border-[#2D264E] text-xs text-[#A5A0C8]">
                  <span>Verified by {mem.verified_by}</span>
                  <span className="text-[#22C55E] font-mono font-bold">Used {mem.times_reused} times</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────── */}
      {/* VIEW 3: List View (Searchable Table)                          */}
      {/* ───────────────────────────────────────────────────────────── */}
      {viewMode === 'list' && (
        <div className="bg-[#141224] border border-[#2D264E] rounded-3xl shadow-xl overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#1E1938] border-b border-[#2D264E] text-[#A5A0C8] font-mono text-[11px]">
              <tr>
                <th className="p-4">ID & Title</th>
                <th className="p-4">Category</th>
                <th className="p-4">Verified By</th>
                <th className="p-4">Times Reused</th>
                <th className="p-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2D264E]">
              {filteredMemories.map((mem) => (
                <tr
                  key={mem.id}
                  onClick={() => setActiveMemory(mem)}
                  className="hover:bg-white/[0.02] cursor-pointer transition-colors"
                >
                  <td className="p-4">
                    <span className="font-mono text-[#8B5CF6] font-bold mr-2">{mem.id}</span>
                    <strong className="text-white">{mem.title}</strong>
                  </td>
                  <td className="p-4">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#8B5CF6]/15 text-[#C4B5FD]">
                      {mem.category}
                    </span>
                  </td>
                  <td className="p-4 text-[#A5A0C8]">{mem.verified_by}</td>
                  <td className="p-4 font-mono text-[#22C55E] font-bold">{mem.times_reused}x</td>
                  <td className="p-4 text-right text-[#C4B5FD] font-semibold">View →</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────── */}
      {/* DETAIL MODAL: Structured Memory Deep Dive                     */}
      {/* ───────────────────────────────────────────────────────────── */}
      <AnimatePresence>
        {activeMemory && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
            <m.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-3xl bg-[#141224] border border-[#8B5CF6]/40 rounded-3xl p-6 sm:p-8 space-y-5 shadow-2xl relative max-h-[90vh] overflow-y-auto"
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-4 pb-3 border-b border-[#2D264E]">
                <div>
                  <span className="text-[10px] font-mono uppercase bg-[#8B5CF6]/20 text-[#C4B5FD] px-2.5 py-0.5 rounded-full border border-[#8B5CF6]/30 font-bold">
                    {activeMemory.category} • {activeMemory.id}
                  </span>
                  <h3 className="text-xl font-bold text-white mt-1.5">{activeMemory.title}</h3>
                </div>
                <button
                  onClick={() => setActiveMemory(null)}
                  className="p-1.5 text-[#A5A0C8] hover:text-white rounded-lg hover:bg-white/10"
                >
                  ✕
                </button>
              </div>

              {/* Problem & Symptoms */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div className="p-4 bg-[#1E1938] border border-[#2D264E] rounded-2xl space-y-1">
                  <span className="text-[10px] uppercase font-bold text-[#EF4444] tracking-wider block">
                    Problem Description
                  </span>
                  <p className="text-zinc-200">{activeMemory.problem}</p>
                </div>

                <div className="p-4 bg-[#1E1938] border border-[#2D264E] rounded-2xl space-y-1">
                  <span className="text-[10px] uppercase font-bold text-[#F59E0B] tracking-wider block">
                    Symptoms & Error Signature
                  </span>
                  <p className="text-zinc-200 font-mono text-[11px]">{activeMemory.symptoms}</p>
                </div>
              </div>

              {/* Root Cause */}
              <div className="p-4 bg-[#1E1938] border border-[#2D264E] rounded-2xl space-y-1 text-xs">
                <span className="text-[10px] uppercase font-bold text-[#8B5CF6] tracking-wider block">
                  Root Cause Analysis
                </span>
                <p className="text-zinc-200">{activeMemory.root_cause}</p>
              </div>

              {/* Working Code Patch */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] uppercase font-bold text-[#22C55E] tracking-wider">
                    Working Solution & Code Patch
                  </span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(activeMemory.code_patch);
                      alert('Code patch copied to clipboard!');
                    }}
                    className="text-xs text-[#C4B5FD] hover:text-white font-bold"
                  >
                    Copy Code
                  </button>
                </div>
                <pre className="p-4 bg-[#0B0914] border border-[#2D264E] rounded-2xl font-mono text-zinc-200 overflow-x-auto text-xs">
                  <code>{activeMemory.code_patch}</code>
                </pre>
              </div>

              {/* Related Services & Memories */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-2">
                <div className="p-3 bg-[#0B0914] border border-[#2D264E] rounded-2xl space-y-1.5">
                  <span className="text-[10px] text-[#A5A0C8] font-mono block">Related Services</span>
                  <div className="flex flex-wrap gap-1.5">
                    {activeMemory.related_services.map((s) => (
                      <span key={s} className="px-2 py-0.5 bg-[#1E1938] border border-[#2D264E] text-[#C4B5FD] rounded-lg text-[11px]">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-3 bg-[#0B0914] border border-[#2D264E] rounded-2xl space-y-1.5">
                  <span className="text-[10px] text-[#A5A0C8] font-mono block">Related Standards</span>
                  <div className="flex flex-wrap gap-1.5">
                    {activeMemory.related_memories.map((m) => (
                      <span key={m} className="px-2 py-0.5 bg-[#1E1938] border border-[#2D264E] text-[#22D3EE] rounded-lg text-[11px]">
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between pt-3 border-t border-[#2D264E] text-xs text-[#A5A0C8]">
                <span>
                  Verified by <strong className="text-white">{activeMemory.verified_by}</strong> • Reused {activeMemory.times_reused} times
                </span>
                <button
                  onClick={() => setActiveMemory(null)}
                  className="px-4 py-2 bg-[#8B5CF6] hover:bg-[#7C3AED] text-white font-bold text-xs rounded-xl"
                >
                  Close
                </button>
              </div>
            </m.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
