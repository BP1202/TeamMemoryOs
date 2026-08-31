import { useState } from 'react';
import { m, AnimatePresence } from 'framer-motion';
import { useUIStore } from '@stores/uiStore';
import { UtilityIcons } from '@config/icons';

interface LearningStage {
  title: string;
  detail: string;
  icon: string;
  status: 'pending' | 'in_progress' | 'completed';
}

export function OnboardingModal() {
  const showModal = useUIStore((s) => s.showOnboardingModal);
  const setShowModal = useUIStore((s) => s.setShowOnboardingModal);
  const setCurrentWorkspace = useUIStore((s) => s.setCurrentWorkspace);

  const [step, setStep] = useState<'form' | 'learning' | 'complete'>('form');
  const [companyName, setCompanyName] = useState('SunBots Technologies');
  const [repoUrl, setRepoUrl] = useState('github.com/sunbots/teammemoryos');
  const [teamSize, setTeamSize] = useState('8 Engineers');
  const [techStack, setTechStack] = useState('Python • FastAPI • React • PostgreSQL • IBM Granite');

  const [stages, setStages] = useState<LearningStage[]>([
    { title: 'Connecting GitHub', detail: 'Connecting github.com/sunbots/teammemoryos', icon: '🔗', status: 'pending' },
    { title: 'Scanning Repository', detail: 'Indexing source code and dependency graphs', icon: '📁', status: 'pending' },
    { title: 'Reading ADRs', detail: 'Synthesizing Architecture Decision Records', icon: '📄', status: 'pending' },
    { title: 'Learning Security Policies', detail: 'Analyzing compliance and security constraints', icon: '🛡️', status: 'pending' },
    { title: 'Building Knowledge Graph', detail: 'Connecting services, ADRs, and incidents into semantic graph', icon: '🕸️', status: 'pending' },
    { title: 'Activating AI Co-workers', detail: 'Initializing PR Guardian, Debugger, & Architect agents', icon: '🤖', status: 'pending' },
  ]);

  const handleStartLearning = async () => {
    setCurrentWorkspace(companyName);
    setStep('learning');

    // Sequential animation for WOW effect
    for (let i = 0; i < 6; i++) {
      setStages((prev) =>
        prev.map((st, idx) => {
          if (idx < i) return { ...st, status: 'completed' };
          if (idx === i) return { ...st, status: 'in_progress' };
          return { ...st, status: 'pending' };
        })
      );
      await new Promise((r) => setTimeout(r, 650));
    }

    setStages((prev) => prev.map((st) => ({ ...st, status: 'completed' })));
    setStep('complete');
  };

  const handleFinish = () => {
    setShowModal(false);
    setStep('form');
  };

  if (!showModal) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <m.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-full max-w-2xl bg-[#161327] border border-[#2D264E] rounded-3xl shadow-2xl shadow-purple-950/60 overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#2A2447] bg-[#1E1938]">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-purple-500 via-indigo-500 to-purple-700 flex items-center justify-center shadow-lg shadow-purple-500/25 text-white font-bold">
              TM
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">
                {step === 'form' && 'Create Engineering Workspace'}
                {step === 'learning' && 'AI Learning Workspace...'}
                {step === 'complete' && 'Workspace Ready! 🚀'}
              </h2>
              <p className="text-xs text-[#A5A0C8]">
                {step === 'form' && 'Teach TeamMemoryOS about your codebase and engineering policies'}
                {step === 'learning' && 'AI Co-worker is synthesizing repository memory'}
                {step === 'complete' && 'Your AI Co-worker is grounded with team knowledge'}
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowModal(false)}
            className="p-1.5 text-[#A5A0C8] hover:text-white rounded-lg hover:bg-white/5 transition-colors"
          >
            <UtilityIcons.Close className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <AnimatePresence mode="wait">
            {step === 'form' && (
              <m.div
                key="form"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 10 }}
                className="space-y-4"
              >
                <div>
                  <label className="block text-xs font-medium text-zinc-300 mb-1.5">
                    Company / Organization Name
                  </label>
                  <input
                    type="text"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                    placeholder="e.g. SunBots Technologies"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-zinc-300 mb-1.5">
                      Repository URL
                    </label>
                    <input
                      type="text"
                      value={repoUrl}
                      onChange={(e) => setRepoUrl(e.target.value)}
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-zinc-300 mb-1.5">
                      Team Size
                    </label>
                    <input
                      type="text"
                      value={teamSize}
                      onChange={(e) => setTeamSize(e.target.value)}
                      className="w-full bg-black/40 border border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-zinc-300 mb-1.5">
                    Tech Stack & AI Engine
                  </label>
                  <input
                    type="text"
                    value={techStack}
                    onChange={(e) => setTechStack(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="p-4 bg-indigo-950/30 border border-indigo-500/20 rounded-xl flex items-start gap-3">
                  <span className="text-xl">🤖</span>
                  <div className="text-xs text-indigo-200">
                    <p className="font-semibold text-indigo-100 mb-0.5">
                      "I'll learn your engineering workspace."
                    </p>
                    <p className="text-indigo-300/80">
                      TeamMemoryOS will index 324 code files, 12 ADRs, and 18 security policies into a pgvector semantic graph.
                    </p>
                  </div>
                </div>

                <div className="pt-2 flex justify-end gap-3">
                  <button
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 text-sm text-zinc-400 hover:text-white font-medium transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleStartLearning}
                    className="px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white text-sm font-semibold rounded-lg shadow-lg shadow-indigo-500/25 transition-all flex items-center gap-2"
                  >
                    <span>Start AI Learning</span>
                    <UtilityIcons.ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </m.div>
            )}

            {step === 'learning' && (
              <m.div
                key="learning"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-3.5 py-2"
              >
                <div className="space-y-2.5">
                  {stages.map((st) => (
                    <div
                      key={st.title}
                      className={`p-3 rounded-xl border flex items-center justify-between transition-all duration-300 ${
                        st.status === 'in_progress'
                          ? 'bg-indigo-950/40 border-indigo-500/50 shadow-md shadow-indigo-500/10'
                          : st.status === 'completed'
                          ? 'bg-emerald-950/20 border-emerald-500/30'
                          : 'bg-white/[0.02] border-white/5 opacity-50'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xl">{st.icon}</span>
                        <div>
                          <p className="text-xs font-semibold text-white">{st.title}</p>
                          <p className="text-[11px] text-zinc-400">{st.detail}</p>
                        </div>
                      </div>

                      <div>
                        {st.status === 'completed' && (
                          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                            ✓ Done
                          </span>
                        )}
                        {st.status === 'in_progress' && (
                          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded-full animate-pulse">
                            Processing...
                          </span>
                        )}
                        {st.status === 'pending' && (
                          <span className="text-[11px] text-zinc-600 font-mono">Queued</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </m.div>
            )}

            {step === 'complete' && (
              <m.div
                key="complete"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="space-y-5 text-center py-2"
              >
                <div className="h-16 w-16 mx-auto rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-3xl shadow-lg shadow-emerald-500/20 animate-bounce">
                  ✨
                </div>

                <div>
                  <h3 className="text-lg font-bold text-white mb-1">
                    AI Learned {companyName}
                  </h3>
                  <p className="text-xs text-zinc-400">
                    Repository graph and historical engineering context successfully compiled.
                  </p>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-left">
                  <div className="p-3 bg-white/[0.03] border border-white/10 rounded-xl">
                    <span className="text-[10px] text-zinc-400 uppercase tracking-wider block">Indexed Files</span>
                    <span className="text-lg font-bold text-white font-mono">324</span>
                  </div>
                  <div className="p-3 bg-white/[0.03] border border-white/10 rounded-xl">
                    <span className="text-[10px] text-zinc-400 uppercase tracking-wider block">ADRs Learned</span>
                    <span className="text-lg font-bold text-indigo-400 font-mono">12</span>
                  </div>
                  <div className="p-3 bg-white/[0.03] border border-white/10 rounded-xl">
                    <span className="text-[10px] text-zinc-400 uppercase tracking-wider block">Security Policies</span>
                    <span className="text-lg font-bold text-emerald-400 font-mono">18</span>
                  </div>
                  <div className="p-3 bg-white/[0.03] border border-white/10 rounded-xl">
                    <span className="text-[10px] text-zinc-400 uppercase tracking-wider block">Connected Services</span>
                    <span className="text-lg font-bold text-purple-400 font-mono">7</span>
                  </div>
                  <div className="p-3 bg-white/[0.03] border border-white/10 rounded-xl col-span-2 sm:col-span-2">
                    <span className="text-[10px] text-zinc-400 uppercase tracking-wider block">Active AI Co-workers</span>
                    <span className="text-sm font-semibold text-white">PR Guardian • Debugger • Architect • Auditor</span>
                  </div>
                </div>

                <button
                  onClick={handleFinish}
                  className="w-full py-3 bg-gradient-to-r from-emerald-500 to-indigo-600 hover:from-emerald-600 hover:to-indigo-700 text-white font-semibold text-sm rounded-xl shadow-lg shadow-emerald-500/20 transition-all"
                >
                  Enter Mission Control 🚀
                </button>
              </m.div>
            )}
          </AnimatePresence>
        </div>
      </m.div>
    </div>
  );
}
