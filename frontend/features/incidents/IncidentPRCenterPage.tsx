import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { m, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@stores/authStore';

interface GameChallenge {
  id: string;
  category: string;
  badge: string;
  title: string;
  scenario: string;
  code_snippet: string;
  options: { text: string; isCorrect: boolean; explanation: string }[];
  xp: number;
  adr_reference: string;
}

interface TeamRank {
  name: string;
  role: string;
  avatar: string;
  level: number;
  xp: number;
  streak: number;
  solved: number;
  badge: string;
  isCurrentUser?: boolean;
}

interface PeerTip {
  id: string;
  author: string;
  role: string;
  avatar: string;
  tag: string;
  title: string;
  tip: string;
  code?: string;
  likes: number;
  time: string;
  isLiked?: boolean;
}

const CHALLENGES: GameChallenge[] = [
  {
    id: 'c1',
    category: 'Database Architecture',
    badge: 'PostgreSQL Standard',
    title: 'Production Outage: Celery Worker Pool Exhaustion',
    scenario: 'Under peak traffic, background workers fail with QueuePool limit of size 10 overflow 10 reached. What is the verified fix according to ADR001?',
    code_snippet: `# Current app/db/session.py
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=5)`,
    options: [
      {
        text: 'Increase pool_size=50, max_overflow=20, and enable pool_pre_ping=True',
        isCorrect: true,
        explanation: 'Correct! pool_pre_ping=True auto-reconnects dead sockets and pool_size=50 supports concurrent async workers without starvation.',
      },
      {
        text: 'Set pool_size=0 to disable connection pooling completely',
        isCorrect: false,
        explanation: 'Disabling connection pooling creates a new TCP handshake per query and crashes the PostgreSQL cluster under moderate traffic.',
      },
      {
        text: 'Restart PostgreSQL every 10 minutes with a cron job',
        isCorrect: false,
        explanation: 'Dangerous antipattern! Scheduled restarts drop active transactions and corrupt uncommitted write operations.',
      },
    ],
    xp: 60,
    adr_reference: 'ADR001: Database & Engine Sizing Standard',
  },
  {
    id: 'c2',
    category: 'Security & Auth',
    badge: 'Zero Trust Auth',
    title: 'Vulnerability: Unverified JWT Algorithm Substitution',
    scenario: 'A penetration test revealed that attackers could forge JWTs if the verification algorithm is unspecified. What is our team security standard?',
    code_snippet: `# Vulnerable auth decoding
jwt.decode(token, SECRET_KEY)`,
    options: [
      {
        text: 'Explicitly enforce algorithms=["HS256"] and set leeway=10 in decode call',
        isCorrect: true,
        explanation: 'Mandatory per Security Standard! Preventing algorithm switching prevents none-algorithm bypass exploits.',
      },
      {
        text: 'Decode the token header with base64 without checking signature',
        isCorrect: false,
        explanation: 'This completely skips cryptography and trusts untrusted user input directly.',
      },
      {
        text: 'Send the secret key in the request headers from client frontend',
        isCorrect: false,
        explanation: 'Exposing SECRET_KEY to the client allows any user to forge arbitrary admin credentials.',
      },
    ],
    xp: 75,
    adr_reference: 'ADR002: JWT Zero-Trust Signature Protocol',
  },
  {
    id: 'c3',
    category: 'Distributed Systems',
    badge: 'Concurrency Standard',
    title: 'Double-Spending Bug on Concurrent Stripe Webhooks',
    scenario: 'Two Stripe invoice webhooks arrived in the same millisecond, triggering duplicate database credit top-ups. How do we prevent this race condition?',
    code_snippet: `# Current handler without distributed locking
async def handle_stripe_webhook(event):
    credit_user(event.user_id, event.amount)`,
    options: [
      {
        text: 'Acquire a Redis distributed Redlock on f"billing:{user_id}" with 10s TTL',
        isCorrect: true,
        explanation: 'Redlock guarantees mutual exclusion across all async uvicorn worker instances simultaneously.',
      },
      {
        text: 'Add a 3 second time.sleep() delay before processing',
        isCorrect: false,
        explanation: 'Arbitrary sleep creates latency and does not eliminate the race condition under load.',
      },
      {
        text: 'Ignore webhook events if another webhook arrived in the last 1 second',
        isCorrect: false,
        explanation: 'Dropping real webhook payments causes customer balance desynchronization.',
      },
    ],
    xp: 85,
    adr_reference: 'ADR003: Redis Redlock Mutual Exclusion',
  },
  {
    id: 'c4',
    id: 'tip-1',
    author: 'Sarah Connor',
    role: 'Tech Lead',
    avatar: '🎯',
    tag: 'Database Gotcha',
    title: 'Silent Socket Drops on Cloud RDS',
    tip: 'When running async SQLAlchemy engines in long-lived workers, always enable pool_pre_ping=True and pool_recycle=3600. AWS RDS silently terminates idle TCP connections after 15 minutes, causing sporadic 500 DisconnectionErrors without pre-ping.',
    code: 'create_engine(DB_URL, pool_pre_ping=True, pool_recycle=3600)',
    likes: 18,
    time: '2h ago',
  },
  {
    id: 'tip-2',
    author: 'Alex Vance',
    role: 'Workspace Owner',
    avatar: '👑',
    tag: 'Security Rule',
    title: 'Docker Image Layer Secrets Leak',
    tip: 'Never use ENV DATABASE_KEY="secret" inside Dockerfiles. Anyone with read access to the image can inspect full plain-text layers via "docker history <image>". Always inject credentials using docker-compose env_file or runtime environment secrets.',
    code: '# Correct: env_file: .env (added to .gitignore)',
    likes: 24,
    time: '5h ago',
  },
  {
    id: 'tip-3',
    author: 'Morgan Chase',
    role: 'Security Auditor',
    avatar: '🛡️',
    tag: 'Concurrency Hack',
    title: 'Redis Lock try/finally Pattern',
    tip: 'Whenever acquiring a distributed Redis lock for webhook processing, ALWAYS wrap worker logic in a try...finally block to guarantee lock release. If your worker crashes unhandled, other threads will deadlock until the TTL expires!',
    code: `lock = redis.lock("inv:123", timeout=15)
try:
    process_payment()
finally:
    lock.release()`,
    likes: 15,
    time: 'Yesterday',
  },
  {
    id: 'tip-4',
    author: 'Devin Thorne',
    role: 'Developer',
    avatar: '💻',
    tag: 'FastAPI Performance',
    title: 'Avoid Blocking Calls in async def Routes',
    tip: 'In FastAPI, never call synchronous blocking libraries (like requests.get or time.sleep) inside an async def route. It blocks the entire single-threaded asyncio event loop! Use httpx.AsyncClient or define the route with standard "def" so FastAPI delegates it to a thread pool.',
    likes: 12,
    time: '2 days ago',
  },
];

export function IncidentPRCenterPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  // Active Organization Metadata
  const activeOrg = useMemo(() => {
    try {
      const stored = localStorage.getItem('teammemory_active_organization');
      if (stored) return JSON.parse(stored);
    } catch (e) {}
    return {
      name: 'cultuss',
      adminName: user?.full_name || 'Jay Patel',
      invitedEmails: ['juli@cultuss.ai', 'janvi@cultuss.ai', 'jeel@cultuss.ai', 'joy@cultuss.ai'],
    };
  }, [user]);

  // Tab State: Quests vs Peer Tips
  const [activeTab, setActiveTab] = useState<'quests' | 'tips'>('quests');

  // Gamification State
  const [currentChallengeIdx, setCurrentChallengeIdx] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [userXp, setUserXp] = useState(615);
  const [streakDays, setStreakDays] = useState(4);
  const [completedChallenges, setCompletedChallenges] = useState<string[]>([]);
  const [isQuestComplete, setIsQuestComplete] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);

  // Peer Tips State
  const [peerTips, setPeerTips] = useState<PeerTip[]>([
    {
      id: 'tip-1',
      author: activeOrg.adminName || 'Jay Patel',
      role: 'Workspace Owner / Lead',
      avatar: 'JP',
      tag: 'PostgreSQL Gotcha',
      title: 'RDS Idle Connection Timeout & Pool Pre-Ping',
      tip: 'AWS RDS terminates idle TCP connections after 300s silently. If your SQLAlchemy engine does not have pool_pre_ping=True, the next query will throw an OperationalError. Always set pool_pre_ping=True in create_engine!',
      code: 'engine = create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300)',
      likes: 31,
      time: '2h ago',
    },
    {
      id: 'tip-2',
      author: Array.isArray(activeOrg.invitedEmails) && activeOrg.invitedEmails[0] ? activeOrg.invitedEmails[0].split('@')[0].toUpperCase() : 'Senior Engineer',
      role: 'Senior Backend Engineer',
      avatar: 'SE',
      tag: 'Docker Security',
      title: 'Never use ENV for secrets in Dockerfile',
      tip: 'Any variable declared as ENV in a Dockerfile is baked into the image metadata permanently and readable with docker inspect. Use runtime environment variables (.env with docker-compose) or Docker BuildKit secret mounts instead.',
      code: '# Correct: env_file: .env (added to .gitignore)',
      likes: 24,
      time: '5h ago',
    },
    {
      id: 'tip-3',
      author: Array.isArray(activeOrg.invitedEmails) && activeOrg.invitedEmails[1] ? activeOrg.invitedEmails[1].split('@')[0].toUpperCase() : 'Security Lead',
      role: 'Security Auditor',
      avatar: 'SA',
      tag: 'Concurrency Hack',
      title: 'Redis Lock try/finally Pattern',
      tip: 'Whenever acquiring a distributed Redis lock for webhook processing, ALWAYS wrap worker logic in a try...finally block to guarantee lock release. If your worker crashes unhandled, other threads will deadlock until the TTL expires!',
      code: `lock = redis.lock("inv:123", timeout=15)\ntry:\n    process_payment()\nfinally:\n    lock.release()`,
      likes: 15,
      time: 'Yesterday',
    },
  ]);
  const [showTipForm, setShowTipForm] = useState(false);
  const [newTipTitle, setNewTipTitle] = useState('');
  const [newTipText, setNewTipText] = useState('');
  const [newTipTag, setNewTipTag] = useState('Gotcha & Fix');
  const [newTipCode, setNewTipCode] = useState('');

  // Live Team Leaderboard derived dynamically from Active Organization
  const leaderboard = useMemo<TeamRank[]>(() => {
    const currentUserName = user?.full_name || activeOrg.adminName || 'Jay Patel';
    const ranks: TeamRank[] = [
      {
        name: `${currentUserName} (You)`,
        role: user?.role === 'owner' ? 'Workspace Owner / Lead' : 'Senior Engineer',
        avatar: currentUserName.replace(/[^a-zA-Z]/g, '').slice(0, 2).toUpperCase() || 'ME',
        level: 3,
        xp: userXp,
        streak: isQuestComplete ? streakDays + 1 : streakDays,
        solved: 22 + completedChallenges.length,
        badge: 'Architecture Sentinel',
        isCurrentUser: true,
      },
    ];

    if (Array.isArray(activeOrg.members) && activeOrg.members.length > 0) {
      activeOrg.members.forEach((m: any, idx: number) => {
        if (m.name !== currentUserName && !m.name.includes(currentUserName)) {
          ranks.push({
            name: m.name,
            role: m.role || 'Software Engineer',
            avatar: m.name.replace(/[^a-zA-Z]/g, '').slice(0, 2).toUpperCase() || 'EN',
            level: 3 + (idx % 2),
            xp: 540 + idx * 120,
            streak: 3 + idx,
            solved: 15 + idx * 4,
            badge: idx === 0 ? 'Memory Architect' : 'Policy Guardian',
          });
        }
      });
    } else if (Array.isArray(activeOrg.invitedEmails)) {
      activeOrg.invitedEmails.forEach((email: string, idx: number) => {
        const uname = email.split('@')[0];
        const formatted = uname.charAt(0).toUpperCase() + uname.slice(1);
        ranks.push({
          name: formatted,
          role: idx === 0 ? 'Senior Backend Engineer' : 'Fullstack Engineer',
          avatar: formatted.slice(0, 2).toUpperCase(),
          level: 3 + (idx % 2),
          xp: 540 + idx * 120,
          streak: 3 + idx,
          solved: 15 + idx * 4,
          badge: idx === 0 ? 'Memory Architect' : 'Policy Guardian',
        });
      });
    }

    return ranks.sort((a, b) => b.xp - a.xp);
  }, [user, activeOrg, userXp, streakDays, completedChallenges, isQuestComplete]);

  const currentChallenge = CHALLENGES[currentChallengeIdx];

  const handleSelectOption = (idx: number) => {
    if (hasSubmitted) return;
    setSelectedOption(idx);
  };

  const handleSubmitAnswer = () => {
    if (selectedOption === null || hasSubmitted) return;
    setHasSubmitted(true);

    const isCorrect = currentChallenge.options[selectedOption].isCorrect;
    if (isCorrect) {
      setUserXp((prev) => prev + currentChallenge.xp);
      const newCompleted = [...completedChallenges, currentChallenge.id];
      setCompletedChallenges(newCompleted);
      setShowCelebration(true);
      setTimeout(() => setShowCelebration(false), 3500);

      // Check if all challenges completed
      if (newCompleted.length >= CHALLENGES.length) {
        setTimeout(() => {
          setIsQuestComplete(true);
          setStreakDays((prev) => prev + 1);
        }, 1200);
      }
    }
  };

  const handleNextChallenge = () => {
    if (currentChallengeIdx + 1 < CHALLENGES.length) {
      setSelectedOption(null);
      setHasSubmitted(false);
      setCurrentChallengeIdx((prev) => prev + 1);
    } else {
      setIsQuestComplete(true);
    }
  };

  const handleRestartReview = () => {
    setCurrentChallengeIdx(0);
    setSelectedOption(null);
    setHasSubmitted(false);
    setIsQuestComplete(false);
  };

  const handleLikeTip = (id: string) => {
    setPeerTips((prev) =>
      prev.map((t) =>
        t.id === id
          ? { ...t, likes: t.isLiked ? t.likes - 1 : t.likes + 1, isLiked: !t.isLiked }
          : t
      )
    );
  };

  const handlePostTip = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTipTitle.trim() || !newTipText.trim()) return;

    const newTip: PeerTip = {
      id: `tip-${Date.now()}`,
      author: 'Devin Thorne (You)',
      role: 'Developer',
      avatar: '💻',
      tag: newTipTag,
      title: newTipTitle,
      tip: newTipText,
      code: newTipCode || undefined,
      likes: 1,
      time: 'Just now',
      isLiked: true,
    };

    setPeerTips([newTip, ...peerTips]);
    setUserXp((prev) => prev + 40);
    setNewTipTitle('');
    setNewTipText('');
    setNewTipCode('');
    setShowTipForm(false);
  };

  return (
    <div className="min-h-screen bg-[#0B0914] text-white p-6 md:p-10 space-y-8 font-sans max-w-7xl mx-auto">
      {/* Top Header with Tab Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#2D264E]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono text-[#A5A0C8] uppercase tracking-wider">
              Engineering Arena
            </span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 font-medium">
              Live Arena
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Daily Quests & Peer Wisdom
          </h1>
          <p className="text-xs text-[#A5A0C8] mt-0.5">
            Sharpen engineering instincts with daily challenges and explore real pro-tips shared by your teammates.
          </p>
        </div>

        {/* Tab Toggle Switcher */}
        <div className="flex items-center gap-1 bg-[#141224] border border-[#2D264E] p-1 rounded-2xl text-xs shadow-xl">
          <button
            onClick={() => setActiveTab('quests')}
            className={`px-4 py-2 font-bold rounded-xl transition-all flex items-center gap-1.5 ${
              activeTab === 'quests'
                ? 'bg-[#8B5CF6] text-white shadow-md shadow-[#8B5CF6]/20'
                : 'text-[#A5A0C8] hover:text-white'
            }`}
          >
            <span>Daily Challenges</span>
            <span className="text-[10px] font-mono bg-white/20 px-1.5 py-0.2 rounded-full">
              {completedChallenges.length}/4
            </span>
          </button>

          <button
            onClick={() => setActiveTab('tips')}
            className={`px-4 py-2 font-bold rounded-xl transition-all flex items-center gap-1.5 ${
              activeTab === 'tips'
                ? 'bg-[#8B5CF6] text-white shadow-md shadow-[#8B5CF6]/20'
                : 'text-[#A5A0C8] hover:text-white'
            }`}
          >
            <span>Peer Pro-Tips</span>
            <span className="text-[10px] font-mono bg-white/20 px-1.5 py-0.2 rounded-full">
              {peerTips.length}
            </span>
          </button>
        </div>
      </div>

      {/* Gamification Bar: Level, XP, Streak */}
      <div className="bg-[#141224] border border-[#2D264E] rounded-3xl p-5 sm:p-6 shadow-xl flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="h-11 w-11 rounded-2xl bg-gradient-to-br from-[#8B5CF6] to-[#6D28D9] flex items-center justify-center text-xs font-bold font-mono text-white shadow-lg shadow-[#8B5CF6]/30">
            {user?.full_name ? user.full_name.replace(/[^a-zA-Z]/g, '').slice(0, 2).toUpperCase() : 'ME'}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-white">
                {user?.full_name || activeOrg.adminName || 'Engineer'}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 font-bold">
                {userXp} XP
              </span>
            </div>
            <p className="text-xs text-[#A5A0C8]">
              {user?.role === 'owner' ? 'Workspace Owner / Lead' : 'Level 3 SRE Engineer'} • 135 XP to Level 4
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right hidden sm:block">
            <span className="text-[10px] font-mono text-[#A5A0C8] block uppercase">Streak</span>
            <span className="text-sm font-bold text-amber-400 font-mono">
              {streakDays} Days
            </span>
          </div>
          <div className="text-right">
            <span className="text-[10px] font-mono text-[#A5A0C8] block uppercase">Progress</span>
            <span className="text-sm font-bold text-[#22D3EE] font-mono">
              {isQuestComplete ? '4 / 4 Complete' : `${completedChallenges.length} / 4 Challenges`}
            </span>
          </div>
        </div>
      </div>

      {/* ───────────────────────────────────────────────────────────── */}
      {/* TAB 1: DAILY QUESTS & LEADERBOARD                             */}
      {/* ───────────────────────────────────────────────────────────── */}
      {activeTab === 'quests' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column (8 cols): Interactive Challenge Card OR Quest Completion Screen */}
          <div className="lg:col-span-8 space-y-6">
            {!isQuestComplete ? (
              <m.div
                key={currentChallenge.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-[#141224] border border-[#8B5CF6]/40 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6 relative overflow-hidden"
              >
                {/* Challenge Counter & Badge */}
                <div className="flex items-center justify-between pb-3 border-b border-[#2D264E]">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-[#8B5CF6]/20 text-[#C4B5FD] border border-[#8B5CF6]/30 font-bold">
                      Challenge {currentChallengeIdx + 1} of {CHALLENGES.length}
                    </span>
                    <span className="text-xs font-mono text-[#A5A0C8]">
                      {currentChallenge.badge}
                    </span>
                  </div>
                  <span className="text-xs font-mono font-bold text-[#22C55E] bg-[#22C55E]/10 border border-[#22C55E]/20 px-2.5 py-0.5 rounded-full">
                    +{currentChallenge.xp} XP
                  </span>
                </div>

                {/* Question Details */}
                <div className="space-y-3 text-left">
                  <h2 className="text-lg sm:text-xl font-bold text-white leading-snug">
                    {currentChallenge.title}
                  </h2>
                  <p className="text-xs sm:text-sm text-[#A5A0C8] leading-relaxed">
                    {currentChallenge.scenario}
                  </p>

                  {/* Code Snippet */}
                  {currentChallenge.code_snippet && (
                    <div className="bg-[#0B0914] border border-[#2D264E] rounded-2xl p-4 font-mono text-xs text-[#C4B5FD] overflow-x-auto shadow-inner">
                      <pre>{currentChallenge.code_snippet}</pre>
                    </div>
                  )}
                </div>

                {/* Multiple Choice Options */}
                <div className="space-y-3 pt-2 text-left">
                  <span className="text-[10px] uppercase font-mono text-[#A5A0C8] font-bold block">
                    Select the Verified Fix:
                  </span>
                  {currentChallenge.options.map((opt, idx) => {
                    const isSelected = selectedOption === idx;
                    let optionStyle = 'bg-[#1E1938] border-[#2D264E] hover:border-[#8B5CF6]/60 text-white';

                    if (hasSubmitted) {
                      if (opt.isCorrect) {
                        optionStyle = 'bg-[#22C55E]/15 border-[#22C55E] text-white shadow-lg shadow-[#22C55E]/10';
                      } else if (isSelected && !opt.isCorrect) {
                        optionStyle = 'bg-rose-500/15 border-rose-500 text-white';
                      } else {
                        optionStyle = 'bg-[#141224] border-[#2D264E] text-[#A5A0C8] opacity-50';
                      }
                    } else if (isSelected) {
                      optionStyle = 'bg-[#8B5CF6]/20 border-[#8B5CF6] text-white ring-2 ring-[#8B5CF6]/30';
                    }

                    return (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleSelectOption(idx)}
                        disabled={hasSubmitted}
                        className={`w-full p-4 rounded-2xl border transition-all text-left text-xs sm:text-sm flex items-start gap-3 ${optionStyle}`}
                      >
                        <span className="h-5 w-5 rounded-full border border-current flex items-center justify-center text-xs flex-shrink-0 mt-0.5 font-mono">
                          {isSelected ? '●' : '○'}
                        </span>
                        <div className="space-y-1">
                          <p className="font-medium leading-relaxed">{opt.text}</p>
                          {hasSubmitted && (opt.isCorrect || isSelected) && (
                            <p className={`text-xs mt-1 font-mono ${opt.isCorrect ? 'text-[#22C55E]' : 'text-rose-400'}`}>
                              {opt.explanation}
                            </p>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>

                {/* Submit & Next Challenge Action Controls */}
                <div className="pt-4 border-t border-[#2D264E] flex items-center justify-between">
                  <span className="text-[10px] font-mono text-[#A5A0C8]">
                    Grounded in: <strong className="text-[#C4B5FD]">{currentChallenge.adr_reference}</strong>
                  </span>

                  {!hasSubmitted ? (
                    <button
                      type="button"
                      onClick={handleSubmitAnswer}
                      disabled={selectedOption === null}
                      className="px-6 py-2.5 bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] disabled:opacity-40 text-white font-bold text-xs rounded-xl shadow-lg shadow-[#8B5CF6]/25 transition-all"
                    >
                      Submit Fix →
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={handleNextChallenge}
                      className="px-6 py-2.5 bg-[#22C55E] hover:bg-emerald-600 text-white font-bold text-xs rounded-xl shadow-lg shadow-[#22C55E]/25 transition-all animate-bounce"
                    >
                      {currentChallengeIdx + 1 < CHALLENGES.length ? 'Next Challenge →' : 'Complete Quest 🏆'}
                    </button>
                  )}
                </div>
              </m.div>
            ) : (
              /* Victory Screen */
              <m.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-[#141224] border border-[#22C55E]/50 rounded-3xl p-8 sm:p-10 shadow-2xl text-center space-y-6"
              >
                <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-[#22C55E]/15 border border-[#22C55E]/30 rounded-full text-xs font-mono text-[#22C55E] font-bold">
                  <span>✓ Daily Quest Complete</span>
                </div>

                <div className="space-y-2">
                  <h2 className="text-2xl sm:text-3xl font-black text-white">
                    Engineering Instincts Mastered!
                  </h2>
                  <p className="text-xs sm:text-sm text-[#A5A0C8] max-w-md mx-auto">
                    You resolved all 4 critical architecture scenarios grounded in verified team memory guidelines.
                  </p>
                </div>

                {/* Score & Streak Rewards */}
                <div className="grid grid-cols-2 gap-4 max-w-md mx-auto text-left font-mono text-xs">
                  <div className="p-4 bg-[#0B0914] border border-[#2D264E] rounded-2xl space-y-1">
                    <span className="text-[10px] text-[#A5A0C8] block">Total XP Earned</span>
                    <span className="text-xl font-extrabold text-[#22C55E]">+270 XP</span>
                  </div>
                  <div className="p-4 bg-[#0B0914] border border-[#2D264E] rounded-2xl space-y-1">
                    <span className="text-[10px] text-[#A5A0C8] block">Solving Streak</span>
                    <span className="text-xl font-extrabold text-amber-400">{streakDays} Days</span>
                  </div>
                </div>

                {/* Standards Mastered Checklist */}
                <div className="p-5 bg-[#0B0914] border border-[#2D264E] rounded-2xl text-left space-y-2 max-w-xl mx-auto text-xs">
                  <span className="text-[10px] uppercase font-mono text-[#A5A0C8] font-bold block mb-1">
                    Architecture Standards Mastered:
                  </span>
                  <p className="text-[#22C55E] flex items-center gap-2">
                    <span>✓</span> ADR001: PostgreSQL QueuePool Sizing & Connection pre-ping
                  </p>
                  <p className="text-[#22C55E] flex items-center gap-2">
                    <span>✓</span> ADR002: JWT HS256 Zero-Trust Decoding & Leeway
                  </p>
                  <p className="text-[#22C55E] flex items-center gap-2">
                    <span>✓</span> ADR003: Redis Distributed Redlock Concurrency
                  </p>
                  <p className="text-[#22C55E] flex items-center gap-2">
                    <span>✓</span> POL-03: Zero Secrets in Source / Docker Images
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => navigate('/knowledge')}
                    className="w-full sm:w-auto px-6 py-3.5 bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white font-bold text-xs rounded-xl shadow-lg shadow-[#8B5CF6]/25 transition-all"
                  >
                    Explore Memory Book →
                  </button>
                  <button
                    type="button"
                    onClick={handleRestartReview}
                    className="w-full sm:w-auto px-6 py-3.5 bg-[#1E1938] hover:bg-[#2D264F] border border-[#2D264E] text-[#C4B5FD] font-semibold text-xs rounded-xl transition-all"
                  >
                    Review Quest Challenges
                  </button>
                </div>
              </m.div>
            )}
          </div>

          {/* Right Column (4 cols): Live Team Leaderboard & Today's Quests */}
          <div className="lg:col-span-4 space-y-5">
            {/* Live Leaderboard */}
            <div className="bg-[#141224] border border-[#2D264E] rounded-3xl p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-[#2D264E]">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  Team Leaderboard
                </h3>
                <span className="text-[10px] font-mono text-[#22C55E]">Live Sync</span>
              </div>

              <div className="space-y-3">
                {leaderboard.map((item, idx) => (
                  <div
                    key={item.name}
                    className={`p-3.5 rounded-2xl border transition-all ${
                      item.isCurrentUser
                        ? 'bg-[#8B5CF6]/15 border-[#8B5CF6]/50 shadow-md shadow-[#8B5CF6]/15'
                        : 'bg-[#1E1938] border-[#2D264E]'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold font-mono text-[#A5A0C8]">#{idx + 1}</span>
                        <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-[#8B5CF6] to-[#6D28D9] text-white flex items-center justify-center text-[10px] font-bold font-mono">
                          {item.avatar}
                        </div>
                        <div>
                          <p className="text-xs font-bold text-white flex items-center gap-1.5">
                            {item.name}
                            {item.isCurrentUser && (
                              <span className="text-[9px] font-mono bg-[#8B5CF6] text-white px-1.5 rounded-full">YOU</span>
                            )}
                          </p>
                          <p className="text-[10px] text-[#A5A0C8] font-mono">{item.badge}</p>
                        </div>
                      </div>
                      <div className="text-right font-mono">
                        <span className="text-xs font-bold text-[#22C55E] block">{item.xp} XP</span>
                        <span className="text-[10px] text-amber-400">Streak {item.streak}d</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Today's Quests Checklist */}
            <div className="bg-[#141224] border border-[#2D264E] rounded-3xl p-6 shadow-xl space-y-3">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <span>🎯</span> Today's Engineering Quests
              </h3>
              <div className="space-y-2 text-xs">
                <div className="p-3 bg-[#1E1938] border border-[#2D264E] rounded-xl flex items-center justify-between">
                  <div>
                    <p className="font-bold text-white">Complete 4 Memory Challenges</p>
                    <p className="text-[10px] text-[#A5A0C8]">+270 XP Reward</p>
                  </div>
                  <span className="text-xs text-[#22C55E] font-bold">
                    {isQuestComplete ? '✓ Completed' : `${completedChallenges.length}/4 Done`}
                  </span>
                </div>
                <div className="p-3 bg-[#1E1938] border border-[#2D264E] rounded-xl flex items-center justify-between">
                  <div>
                    <p className="font-bold text-white">Share 1 Engineering Pro-Tip</p>
                    <p className="text-[10px] text-[#A5A0C8]">+40 XP Reward</p>
                  </div>
                  <span className="text-xs text-[#C4B5FD] font-mono font-bold">Available</span>
                </div>
                <div className="p-3 bg-[#1E1938] border border-[#2D264E] rounded-xl flex items-center justify-between">
                  <div>
                    <p className="font-bold text-white">Maintain 5-Day Streak</p>
                    <p className="text-[10px] text-[#A5A0C8]">🔥 Active Streak</p>
                  </div>
                  <span className="text-xs text-amber-400 font-mono font-bold">5 Days</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ───────────────────────────────────────────────────────────── */}
      {/* TAB 2: PEER PRO-TIPS & SECRET HACKS                           */}
      {/* ───────────────────────────────────────────────────────────── */}
      {activeTab === 'tips' && (
        <div className="bg-[#141224] border border-[#2D264E] rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#2D264E]">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono text-[#8B5CF6] uppercase tracking-wider font-bold">
                  Peer Wisdom & Knowledge Exchange
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#8B5CF6]/15 text-[#C4B5FD] border border-[#8B5CF6]/30 font-medium">
                  Live Community Feed
                </span>
              </div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <span>💡</span> Engineering Pro-Tips, Gotchas & Secret Hacks
              </h2>
              <p className="text-xs text-[#A5A0C8] mt-0.5">
                Real-world tricks and architectural learnings shared by your teammates to help everyone grow.
              </p>
            </div>

            <button
              onClick={() => setShowTipForm((prev) => !prev)}
              className="px-5 py-2.5 bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white font-bold text-xs rounded-xl shadow-lg shadow-[#8B5CF6]/25 transition-all flex items-center gap-2 flex-shrink-0"
            >
              <span>✍️ Share a Pro-Tip (+40 XP)</span>
            </button>
          </div>

          {/* Share Pro-Tip Form */}
          {showTipForm && (
            <form
              onSubmit={handlePostTip}
              className="p-5 bg-[#1E1938] border border-[#8B5CF6]/50 rounded-2xl space-y-3 animate-fade-in"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  Share what you learned with teammates (+40 XP)
                </h3>
                <span className="text-[10px] text-[#A5A0C8] font-mono">Visible to entire team</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <input
                  type="text"
                  value={newTipTitle}
                  onChange={(e) => setNewTipTitle(e.target.value)}
                  placeholder="Tip Title (e.g. Postgres Connection Timeout Trick)"
                  className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none"
                />
                <select
                  value={newTipTag}
                  onChange={(e) => setNewTipTag(e.target.value)}
                  className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none"
                >
                  <option value="Gotcha & Fix">Gotcha & Fix</option>
                  <option value="Database Hack">Database Hack</option>
                  <option value="Security Rule">Security Rule</option>
                  <option value="Concurrency Hack">Concurrency Hack</option>
                  <option value="Performance Trick">Performance Trick</option>
                </select>
              </div>

              <textarea
                value={newTipText}
                onChange={(e) => setNewTipText(e.target.value)}
                placeholder="Explain the gotcha, what caused it, and what engineers should do..."
                rows={2}
                className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl p-3 text-xs text-white placeholder-zinc-500 focus:outline-none resize-none"
              />

              <input
                type="text"
                value={newTipCode}
                onChange={(e) => setNewTipCode(e.target.value)}
                placeholder="Optional code snippet or command (e.g. pool_pre_ping=True)"
                className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2 text-xs text-zinc-300 font-mono placeholder-zinc-500 focus:outline-none"
              />

              <div className="flex items-center justify-end gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setShowTipForm(false)}
                  className="px-4 py-2 bg-transparent text-xs text-[#A5A0C8] hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!newTipTitle.trim() || !newTipText.trim()}
                  className="px-5 py-2 bg-[#22C55E] hover:bg-emerald-600 text-white font-bold text-xs rounded-xl transition-all shadow-md shadow-[#22C55E]/20 disabled:opacity-40"
                >
                  Publish Pro-Tip →
                </button>
              </div>
            </form>
          )}

          {/* Pro-Tips Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {peerTips.map((tip) => (
              <div
                key={tip.id}
                className="p-5 bg-[#1E1938] border border-[#2D264E] rounded-2xl space-y-3.5 flex flex-col justify-between hover:border-[#8B5CF6]/50 transition-all shadow-lg"
              >
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{tip.avatar}</span>
                      <div>
                        <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                          {tip.author}
                          <span className="text-[9px] font-mono text-[#A5A0C8]">• {tip.role}</span>
                        </h4>
                        <span className="text-[10px] text-[#A5A0C8] font-mono">{tip.time}</span>
                      </div>
                    </div>

                    <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-[#8B5CF6]/15 text-[#C4B5FD] border border-[#8B5CF6]/30 font-semibold">
                      {tip.tag}
                    </span>
                  </div>

                  <div className="space-y-1">
                    <h3 className="text-sm font-bold text-white">{tip.title}</h3>
                    <p className="text-xs text-zinc-300 leading-relaxed">{tip.tip}</p>
                  </div>

                  {tip.code && (
                    <pre className="p-3 bg-[#0B0914] border border-[#2D264E] rounded-xl font-mono text-[11px] text-emerald-300 overflow-x-auto whitespace-pre-wrap">
                      <code>{tip.code}</code>
                    </pre>
                  )}
                </div>

                {/* Likes & Helpful Button */}
                <div className="pt-2 border-t border-[#2D264E] flex items-center justify-between">
                  <span className="text-[11px] text-[#A5A0C8] font-mono">
                    {tip.likes} engineers found this helpful
                  </span>

                  <button
                    onClick={() => handleLikeTip(tip.id)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                      tip.isLiked
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40 shadow-sm'
                        : 'bg-[#0B0914] text-[#A5A0C8] hover:text-white border border-[#2D264E] hover:border-[#8B5CF6]/40'
                    }`}
                  >
                    <span>{tip.isLiked ? '❤️ Helpful' : '🤍 Helpful'}</span>
                    <span className="font-mono text-[11px]">{tip.likes}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Celebration Toast Modal */}
      <AnimatePresence>
        {showCelebration && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
            <m.div
              initial={{ scale: 0.8, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.8, opacity: 0, y: -20 }}
              className="bg-[#141224] border border-[#22C55E] rounded-3xl p-6 shadow-2xl shadow-[#22C55E]/30 text-center space-y-2 pointer-events-auto"
            >
              <div className="text-4xl animate-bounce">🏆</div>
              <h3 className="text-base font-bold text-white">Correct Fix! +{currentChallenge?.xp} XP</h3>
              <p className="text-xs text-[#A5A0C8]">
                You grounded the solution in team memory. Leaderboard ranking updated!
              </p>
            </m.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
