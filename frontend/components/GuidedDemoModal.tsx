import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { m } from 'framer-motion';
import { useUIStore } from '@stores/uiStore';
import { UtilityIcons } from '@config/icons';

interface DemoStep {
  stepIndex: number;
  time: string;
  badge: string;
  title: string;
  description: string;
  route: string;
  features: string[];
  keyInsight: string;
  aiAction: string;
}

const DEMO_STEPS: DemoStep[] = [
  {
    stepIndex: 1,
    time: '0:00 - 0:30',
    badge: '1. Workspace Creation',
    title: 'Create "SunBots Technologies" Workspace',
    description:
      'Set up the engineering workspace, connect repositories, and initialize team governance for Alex, Sarah, Devin, and Morgan.',
    route: '/',
    features: [
      'Multi-role workspace for Owner, Tech Lead, Developer, and Auditor',
      'Instant connection to GitHub, PostgreSQL, and developer tools',
      'Role-tailored dashboards with active metrics',
      'Knowledge Health indicator initialized at 98%'
    ],
    keyInsight: 'Establishes a unified collaborative workspace for the whole team.',
    aiAction: 'Setup SunBots Workspace'
  },
  {
    stepIndex: 2,
    time: '0:30 - 1:00',
    badge: '2. Continuous Learning',
    title: 'AI Learns Repository & 18 Engineering Policies',
    description:
      'TeamMemoryOS parses codebase files, indexes ADRs, extracts security policies, and connects services into a living knowledge graph.',
    route: '/knowledge',
    features: [
      '324 source files mapped to 7 microservices',
      '12 ADRs & 18 security policies synthesized into rules',
      'Living semantic knowledge graph with 28 nodes & 42 relations',
      'Interactive visual timeline of team decisions'
    ],
    keyInsight: 'Eliminates weeks of repetitive onboarding and preserves tribal knowledge forever.',
    aiAction: 'Explore Team Knowledge'
  },
  {
    stepIndex: 3,
    time: '1:00 - 1:45',
    badge: '3. Grounded AI Assistant',
    title: 'Ask AI Architecture Questions with Evidence',
    description:
      'Developers query the AI co-worker. AI returns visual cards (Summary, Why, Affected Services, Actions) backed by citations from ADR002 and security.py.',
    route: '/chat',
    features: [
      'Structured response cards with zero scrolling essays',
      'Evidence cards linking directly to ADR002 and source files',
      'Animated multi-stage thinking timeline',
      'Multi-tab workspace with Repository Explorer & Decision Simulator'
    ],
    keyInsight: 'Every AI answer is grounded in verifiable organizational evidence.',
    aiAction: 'Open AI Assistant'
  },
  {
    stepIndex: 4,
    time: '1:45 - 2:20',
    badge: '4. SRE Incident Investigation',
    title: 'Paste Crash Log → Recall Past Incident → 1-Click Patch',
    description:
      'Paste a PostgreSQL pool exhaustion crash log. AI matches past incident INC012 (94% match) and generates a verified configuration fix.',
    route: '/incidents?tab=incident',
    features: [
      'Classification: PostgreSQL Pool Exhaustion',
      'Similar Incident: INC012 (94% match in team knowledge)',
      'Deterministic verified patch for session.py',
      'One Button: "Save Resolution to Team Knowledge"'
    ],
    keyInsight: 'Turns repeated firefighting into instantaneous, permanent learning.',
    aiAction: 'Investigate Crash Log'
  },
  {
    stepIndex: 5,
    time: '2:20 - 2:50',
    badge: '5. PR Guardian Defense',
    title: 'PR Guardian Blocks Merges Violating Policies',
    description:
      'Upload a git diff with raw SQL string formatting. AI PR Guardian detects the policy violation against ADR001, calculates risk, and provides compliant code.',
    route: '/incidents?tab=guardian',
    features: [
      'Risk Scorecard: 88/100 (BLOCKED verdict)',
      'Direct violation detection against ADR001 & SQL injection policy',
      'Service Blast Radius map showing affected dependencies',
      'Interactive Approve / Reject controls with replacement code'
    ],
    keyInsight: 'Automated architectural guardian protecting code quality on every PR.',
    aiAction: 'Review PR with Guardian'
  },
  {
    stepIndex: 6,
    time: '2:50 - 3:00',
    badge: '6. Institutional Memory',
    title: 'Save Resolution $\\to$ AI Remembers Forever',
    description:
      'Clicking save updates the live decision timeline, expands the knowledge graph, and alerts the activity feed. AI never forgets.',
    route: '/knowledge',
    features: [
      'Incident resolution permanently committed to memory bank',
      'Knowledge Graph updates with new incident node and mitigations',
      'Activity feed notifies the engineering team',
      'SOC 2 Type II audit compliance evidence updated'
    ],
    keyInsight: 'The single continuous workflow demonstrating TeamMemoryOS v5 value.',
    aiAction: 'View Updated Memory'
  }
];

export function GuidedDemoModal() {
  const navigate = useNavigate();
  const showModal = useUIStore((s) => s.showGuidedDemoModal);
  const setShowModal = useUIStore((s) => s.setShowGuidedDemoModal);
  const setShowOnboarding = useUIStore((s) => s.setShowOnboardingModal);
  const currentStep = useUIStore((s) => s.guidedDemoStep);
  const setCurrentStep = useUIStore((s) => s.setGuidedDemoStep);

  const [activeStepIndex, setActiveStepIndex] = useState(0);

  useEffect(() => {
    if (currentStep >= 0 && currentStep < DEMO_STEPS.length) {
      setActiveStepIndex(currentStep);
    }
  }, [currentStep]);

  if (!showModal) return null;

  const currentStepData = DEMO_STEPS[activeStepIndex];

  const handleNext = () => {
    if (activeStepIndex < DEMO_STEPS.length - 1) {
      const nextIdx = activeStepIndex + 1;
      setActiveStepIndex(nextIdx);
      setCurrentStep(nextIdx);
      navigate(DEMO_STEPS[nextIdx].route);
    } else {
      setShowModal(false);
      navigate('/knowledge');
    }
  };

  const handlePrev = () => {
    if (activeStepIndex > 0) {
      const prevIdx = activeStepIndex - 1;
      setActiveStepIndex(prevIdx);
      setCurrentStep(prevIdx);
      navigate(DEMO_STEPS[prevIdx].route);
    }
  };

  const handleJumpToStep = (idx: number) => {
    setActiveStepIndex(idx);
    setCurrentStep(idx);
    navigate(DEMO_STEPS[idx].route);
  };

  const handleAction = () => {
    if (activeStepIndex === 0) {
      setShowModal(false);
      setShowOnboarding(true);
    } else {
      navigate(currentStepData.route);
      setShowModal(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <m.div
        initial={{ scale: 0.95, opacity: 0, y: 10 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.95, opacity: 0, y: 10 }}
        className="w-full max-w-3xl bg-[#161327] border border-purple-500/40 rounded-3xl p-6 sm:p-8 shadow-2xl shadow-purple-950/60 space-y-6 text-zinc-100 font-sans relative overflow-hidden"
      >
        {/* Ambient Glow */}
        <div className="absolute -top-24 -right-24 w-72 h-72 bg-purple-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-72 h-72 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />

        {/* Top Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#2A2447] relative z-10">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-purple-500 via-indigo-500 to-purple-700 flex items-center justify-center text-white font-bold shadow-lg shadow-purple-500/30">
              🏆
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white tracking-tight">
                  TeamMemoryOS v5 — 3-Minute Guided Demo
                </h2>
                <span className="text-[10px] font-mono uppercase bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded-full border border-purple-500/30">
                  Winning Story
                </span>
              </div>
              <p className="text-xs text-[#A5A0C8]">
                One continuous workflow: Onboarding $\to$ AI Assistant $\to$ Incident Center $\to$ PR Guardian $\to$ Memory Commit
              </p>
            </div>
          </div>

          <button
            onClick={() => setShowModal(false)}
            className="p-2 text-[#A5A0C8] hover:text-white rounded-xl hover:bg-white/10 transition-colors"
          >
            <UtilityIcons.Close className="h-5 w-5" />
          </button>
        </div>

        {/* Step Progress Indicators */}
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 relative z-10">
          {DEMO_STEPS.map((s, idx) => (
            <button
              key={s.stepIndex}
              onClick={() => handleJumpToStep(idx)}
              className={`p-2.5 rounded-xl text-left transition-all border ${
                activeStepIndex === idx
                  ? 'bg-purple-600/35 border-purple-500 text-white shadow-lg shadow-purple-600/20'
                  : idx < activeStepIndex
                  ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300'
                  : 'bg-[#1E1938] border-[#2D264E] text-[#A5A0C8] hover:bg-[#251F45]'
              }`}
            >
              <div className="flex items-center justify-between text-[10px] font-mono mb-1">
                <span>Step {s.stepIndex}</span>
                <span>{idx < activeStepIndex ? '✓' : s.time.split(' ')[0]}</span>
              </div>
              <p className="text-xs font-semibold truncate">{s.title.split(' ')[0]} {s.title.split(' ')[1]}</p>
            </button>
          ))}
        </div>

        {/* Active Step Showcase Card */}
        <div className="bg-[#1E1938] border border-[#2D264E] rounded-2xl p-6 space-y-4 relative z-10 shadow-inner">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
              {currentStepData.badge} • {currentStepData.time}
            </span>
            <span className="text-xs text-[#A5A0C8] font-mono">
              Workspace Route: <span className="text-purple-200 font-semibold">{currentStepData.route}</span>
            </span>
          </div>

          <div>
            <h3 className="text-lg font-bold text-white tracking-tight">
              {currentStepData.title}
            </h3>
            <p className="text-xs text-[#C4BFDE] mt-1 leading-relaxed">
              {currentStepData.description}
            </p>
          </div>

          {/* Feature Highlights Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2">
            {currentStepData.features.map((feat, idx) => (
              <div
                key={idx}
                className="p-2.5 bg-[#262046] border border-purple-500/20 rounded-xl flex items-start gap-2 text-xs text-zinc-200"
              >
                <span className="text-purple-400 font-bold mt-0.5">✦</span>
                <span>{feat}</span>
              </div>
            ))}
          </div>

          {/* Key Value Callout */}
          <div className="p-3.5 bg-gradient-to-r from-purple-950/50 via-[#262046] to-[#161327] border border-purple-500/30 rounded-xl flex items-center gap-3">
            <span className="text-lg">💡</span>
            <div className="text-xs">
              <span className="font-semibold text-purple-300">Challenge Value: </span>
              <span className="text-zinc-200">{currentStepData.keyInsight}</span>
            </div>
          </div>
        </div>

        {/* Footer Navigation Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 relative z-10">
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrev}
              disabled={activeStepIndex === 0}
              className="px-4 py-2 bg-[#211C3B] hover:bg-[#2D264F] disabled:opacity-30 text-xs font-semibold text-[#A5A0C8] rounded-xl border border-[#2D264E] transition-all"
            >
              ← Previous
            </button>
            <button
              onClick={handleNext}
              className="px-4 py-2 bg-[#211C3B] hover:bg-[#2D264F] text-xs font-semibold text-white rounded-xl border border-purple-500/30 transition-all"
            >
              {activeStepIndex === DEMO_STEPS.length - 1 ? 'Finish Tour' : 'Next Step →'}
            </button>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              onClick={handleAction}
              className="w-full sm:w-auto px-5 py-2.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-purple-600/25 transition-all flex items-center justify-center gap-2"
            >
              <span>🚀 {currentStepData.aiAction}</span>
            </button>
          </div>
        </div>
      </m.div>
    </div>
  );
}
