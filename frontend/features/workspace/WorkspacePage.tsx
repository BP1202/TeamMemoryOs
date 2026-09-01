import { useState } from 'react';
import { m, AnimatePresence } from 'framer-motion';
import { useUIStore } from '@stores/uiStore';
import { useAuthStore } from '@stores/authStore';

interface TeamMember {
  name: string;
  role: string;
  avatar: string;
  memories_created: number;
  problems_solved: number;
  prs_reviewed: number;
  status: string;
}

interface ServiceCard {
  name: string;
  status: 'Healthy' | 'Degraded';
  owner: string;
  endpoints_count: number;
  known_incidents: number;
  memories_count: number;
  description: string;
}

interface RepoConfig {
  repoUrl: string;
  branch: string;
  docPath: string;
  lastSync: string;
  status: 'Connected' | 'Syncing';
}

export function WorkspacePage() {
  const currentWorkspace = useUIStore((s) => s.currentWorkspace);
  const setCurrentWorkspace = useUIStore((s) => s.setCurrentWorkspace);
  const user = useAuthStore((s) => s.user);

  // Read active organization metadata
  const [activeOrg, setActiveOrg] = useState(() => {
    try {
      const stored = localStorage.getItem('teammemory_active_organization');
      if (stored) return JSON.parse(stored);
    } catch (e) {
      // pass
    }
    return {
      name: currentWorkspace || 'cultuss',
      adminName: user?.full_name || 'Jay Patel',
      adminEmail: user?.email || 'jay@admin.in',
      invitedEmails: ['juli@cultuss.ai', 'janvi@cultuss.ai', 'jeel@cultuss.ai', 'joy@cultuss.ai'],
      techStack: ['FastAPI', 'PostgreSQL', 'pgvector', 'Docker', 'React', 'Python'],
      repoUrl: 'https://github.com/cultuss/teammemory-os',
      branch: 'main',
      docPath: 'docs/architecture',
    };
  });

  // Setup Workspace Modal State
  const [showSetupModal, setShowSetupModal] = useState(false);
  const [editOrgName, setEditOrgName] = useState(activeOrg.name || 'cultuss');
  const [editRepoUrl, setEditRepoUrl] = useState(activeOrg.repoUrl || 'https://github.com/cultuss/teammemory-os');
  const [editBranch, setEditBranch] = useState(activeOrg.branch || 'main');
  const [editDocPath, setEditDocPath] = useState(activeOrg.docPath || 'docs/architecture');
  const [editTechStack, setEditTechStack] = useState<string[]>(
    Array.isArray(activeOrg.techStack) ? activeOrg.techStack : ['FastAPI', 'PostgreSQL', 'pgvector', 'Docker', 'React']
  );
  const [customTechInput, setCustomTechInput] = useState('');
  const [newInviteEmail, setNewInviteEmail] = useState('');
  const [invitedList, setInvitedList] = useState<string[]>(
    Array.isArray(activeOrg.invitedEmails) ? activeOrg.invitedEmails : ['juli@cultuss.ai', 'janvi@cultuss.ai']
  );
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // Dynamic Members Roster
  const members: TeamMember[] = (() => {
    if (Array.isArray(activeOrg.members) && activeOrg.members.length > 0) {
      return activeOrg.members.map((m: any, idx: number) => ({
        name: m.name,
        role: m.role || 'Software Engineer',
        avatar: m.name.replace(/[^a-zA-Z]/g, '').slice(0, 2).toUpperCase() || 'EN',
        memories_created: m.status?.includes('Pending') ? 0 : 8 + idx * 4,
        problems_solved: m.status?.includes('Pending') ? 0 : 12 + idx * 6,
        prs_reviewed: m.status?.includes('Pending') ? 0 : 15 + idx * 8,
        status: m.status || 'Active Now',
      }));
    }

    const list: TeamMember[] = [
      {
        name: `${activeOrg.adminName || 'Jay Patel'} (Owner)`,
        role: 'Workspace Owner / Lead',
        avatar: (activeOrg.adminName || 'JP').replace(/[^a-zA-Z]/g, '').slice(0, 2).toUpperCase(),
        memories_created: 18,
        problems_solved: 34,
        prs_reviewed: 52,
        status: 'Active Now',
      },
    ];

    if (Array.isArray(activeOrg.invitedEmails)) {
      activeOrg.invitedEmails.forEach((email: string, idx: number) => {
        const username = email.split('@')[0];
        const formattedName = username.charAt(0).toUpperCase() + username.slice(1);
        list.push({
          name: formattedName,
          role: idx === 0 ? 'Senior Backend Engineer' : 'Fullstack Engineer',
          avatar: formattedName.slice(0, 2).toUpperCase(),
          memories_created: 8 + idx * 4,
          problems_solved: 12 + idx * 6,
          prs_reviewed: 15 + idx * 8,
          status: 'Active Now',
        });
      });
    }

    return list;
  })();

  // Dynamic Services Catalog from Organization Tech Stack
  const services: ServiceCard[] = (() => {
    const stack = Array.isArray(activeOrg.techStack) && activeOrg.techStack.length > 0
      ? activeOrg.techStack
      : ['FastAPI', 'PostgreSQL', 'pgvector', 'Docker', 'React', 'Python'];

    return stack.map((tech: string, idx: number) => {
      let desc = `${tech} production architecture integration and verified memory guidelines.`;
      if (tech.toLowerCase().includes('fastapi')) {
        desc = 'FastAPI asynchronous REST API endpoints, Pydantic schemas, and middleware.';
      } else if (tech.toLowerCase().includes('postgres')) {
        desc = 'PostgreSQL database cluster with QueuePool sizing and session management.';
      } else if (tech.toLowerCase().includes('vector')) {
        desc = 'pgvector semantic similarity index for persistent engineering memory retrieval.';
      } else if (tech.toLowerCase().includes('redis')) {
        desc = 'Redis distributed caching and Redlock distributed lock execution.';
      } else if (tech.toLowerCase().includes('docker')) {
        desc = 'Docker multi-stage container build and environment isolation policy.';
      } else if (tech.toLowerCase().includes('react')) {
        desc = 'React client SPA with Tailwind CSS obsidian design tokens.';
      }

      return {
        name: `${tech} Service`,
        status: 'Healthy',
        owner: activeOrg.adminName || 'Jay Patel',
        endpoints_count: 6 + idx * 4,
        known_incidents: 2 + (idx % 3),
        memories_count: 5 + idx * 3,
        description: desc,
      };
    });
  })();

  // Save Workspace Setup Handler
  const handleSaveSetup = (e: React.FormEvent) => {
    e.preventDefault();

    const updated = {
      ...activeOrg,
      name: editOrgName.trim() || activeOrg.name,
      repoUrl: editRepoUrl.trim(),
      branch: editBranch.trim(),
      docPath: editDocPath.trim(),
      techStack: editTechStack,
      invitedEmails: invitedList,
    };

    setActiveOrg(updated);
    setCurrentWorkspace(updated.name);
    try {
      localStorage.setItem('teammemory_active_organization', JSON.stringify(updated));
    } catch (e) {}

    setShowSetupModal(false);
    setToastMsg(`✓ Workspace configuration updated for ${updated.name}`);
    setTimeout(() => setToastMsg(null), 4000);
  };

  const handleToggleTech = (tech: string) => {
    setEditTechStack((prev) =>
      prev.includes(tech) ? prev.filter((t) => t !== tech) : [...prev, tech]
    );
  };

  const handleAddCustomTech = (e: React.KeyboardEvent | React.MouseEvent) => {
    if ('key' in e && e.key !== 'Enter' && e.key !== ',') return;
    e.preventDefault();
    const trimmed = customTechInput.trim().replace(/,/g, '');
    if (trimmed && !editTechStack.includes(trimmed)) {
      setEditTechStack((prev) => [...prev, trimmed]);
      setCustomTechInput('');
    }
  };

  const handleAddInvite = (e?: React.KeyboardEvent | React.MouseEvent) => {
    if (e && 'key' in e && e.key !== 'Enter' && e.key !== ',') return;
    if (e) e.preventDefault();
    const trimmed = newInviteEmail.trim().replace(/,/g, '');
    if (trimmed && !invitedList.includes(trimmed)) {
      setInvitedList((prev) => [...prev, trimmed]);
      setNewInviteEmail('');
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0914] text-white p-6 md:p-10 space-y-8 font-sans max-w-7xl mx-auto">
      {/* Toast Notification */}
      {toastMsg && (
        <div className="fixed top-6 right-6 z-50 px-4 py-3 bg-[#22C55E]/15 border border-[#22C55E]/40 text-[#22C55E] rounded-2xl text-xs font-mono shadow-2xl backdrop-blur-md animate-fade-in flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-[#22C55E]" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Header with Setup Workspace Action */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#2D264E]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono text-[#A5A0C8] uppercase tracking-wider">
              Organization & Infrastructure
            </span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 font-medium">
              Live Workspace
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            {activeOrg.name || currentWorkspace}
          </h1>
          <p className="text-xs text-[#A5A0C8] mt-0.5">
            Engineering team members, connected repositories, and verified service catalog.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Setup Workspace Button */}
          <button
            type="button"
            onClick={() => setShowSetupModal(true)}
            className="px-4 py-2.5 bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white font-bold text-xs rounded-xl shadow-lg shadow-[#8B5CF6]/25 transition-all flex items-center gap-2"
          >
            <span>Setup Workspace</span>
          </button>

          <div className="p-2.5 px-4 bg-[#141224] border border-[#2D264E] rounded-2xl flex items-center gap-4 text-xs font-mono">
            <div>
              <span className="text-[10px] text-[#A5A0C8] block">Team Roster</span>
              <span className="text-white font-bold">{members.length} Engineers</span>
            </div>
            <div className="h-6 w-px bg-[#2D264E]" />
            <div>
              <span className="text-[10px] text-[#A5A0C8] block">Tech Stack</span>
              <span className="text-[#C4B5FD] font-bold">{services.length} Services</span>
            </div>
          </div>
        </div>
      </div>

      {/* Connected Git Repositories Section */}
      <div className="p-5 bg-[#141224] border border-[#2D264E] rounded-3xl space-y-3 shadow-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-[#8B5CF6] font-bold">
              Connected Source Repository
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 font-bold">
              Synced
            </span>
          </div>
          <button
            type="button"
            onClick={() => setShowSetupModal(true)}
            className="text-xs font-mono text-[#8B5CF6] hover:text-[#C4B5FD]"
          >
            Configure →
          </button>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono pt-1">
          <div>
            <span className="text-white font-bold block">{activeOrg.repoUrl || 'https://github.com/cultuss/teammemory-os'}</span>
            <span className="text-[#A5A0C8] text-[11px]">
              Branch: <strong className="text-white">{activeOrg.branch || 'main'}</strong> • Docs: <strong className="text-white">{activeOrg.docPath || 'docs/architecture'}</strong>
            </span>
          </div>
          <span className="text-[#A5A0C8] text-[10px]">Continuous Memory Ingestion Active</span>
        </div>
      </div>

      {/* Team Roster */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white">
              Active Engineering Team
            </h2>
            <p className="text-xs text-[#A5A0C8]">
              Engineers contributing to and grounded in organizational memory.
            </p>
          </div>
          <span className="text-xs font-mono text-[#8B5CF6] font-bold">
            {members.length} Active Members
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {members.map((m) => (
            <div
              key={m.name}
              className="p-5 bg-[#141224] border border-[#2D264E] rounded-2xl space-y-4 hover:border-[#8B5CF6]/50 transition-all shadow-xl"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-[#8B5CF6] to-[#6D28D9] text-white flex items-center justify-center text-xs font-bold font-mono shadow-md shadow-[#8B5CF6]/20">
                    {m.avatar || 'EN'}
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-white">{m.name}</h3>
                    <p className="text-[10px] text-[#A5A0C8] font-mono">{m.role}</p>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-[#2D264E] grid grid-cols-3 gap-2 text-center text-xs font-mono">
                <div className="p-2 bg-[#0B0914] rounded-xl">
                  <span className="text-[10px] text-[#A5A0C8] block">Memories</span>
                  <span className="font-bold text-[#8B5CF6]">{m.memories_created}</span>
                </div>
                <div className="p-2 bg-[#0B0914] rounded-xl">
                  <span className="text-[10px] text-[#A5A0C8] block">Solved</span>
                  <span className="font-bold text-[#22C55E]">{m.problems_solved}</span>
                </div>
                <div className="p-2 bg-[#0B0914] rounded-xl">
                  <span className="text-[10px] text-[#A5A0C8] block">Reviews</span>
                  <span className="font-bold text-[#22D3EE]">{m.prs_reviewed}</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-[10px] font-mono pt-1 text-[#A5A0C8]">
                <span>Status</span>
                <span className="text-[#22C55E] flex items-center gap-1 font-bold">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#22C55E]" />
                  {m.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Services & Tech Stack Catalog */}
      <div className="space-y-4 pt-2">
        <div>
          <h2 className="text-base font-bold text-white">
            Connected Services & Primary Tech Stack
          </h2>
          <p className="text-xs text-[#A5A0C8]">
            Microservices and infrastructure monitored with persistent engineering memory.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {services.map((svc) => (
            <div
              key={svc.name}
              className="p-5 bg-[#141224] border border-[#2D264E] rounded-2xl space-y-3.5 hover:border-[#8B5CF6]/50 transition-all shadow-xl"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-[#22C55E]" />
                  <h3 className="text-sm font-bold text-white">{svc.name}</h3>
                </div>
                <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 font-bold">
                  {svc.status}
                </span>
              </div>

              <p className="text-xs text-[#A5A0C8] leading-relaxed">{svc.description}</p>

              <div className="pt-2 border-t border-[#2D264E] flex items-center justify-between text-xs font-mono text-[#A5A0C8]">
                <span>Owner: <strong className="text-white">{svc.owner}</strong></span>
                <div className="flex items-center gap-3">
                  <span>{svc.endpoints_count} Endpoints</span>
                  <span>•</span>
                  <span className="text-[#C4B5FD]">{svc.memories_count} Memories</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ───────────────────────────────────────────────────────────── */}
      {/* SETUP WORKSPACE MODAL                                         */}
      {/* ───────────────────────────────────────────────────────────── */}
      <AnimatePresence>
        {showSetupModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <m.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#141224] border border-[#8B5CF6]/50 rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 sm:p-8 shadow-2xl space-y-5"
            >
              <div className="flex items-center justify-between pb-3 border-b border-[#2D264E]">
                <div>
                  <h2 className="text-lg font-bold text-white">Setup Workspace</h2>
                  <p className="text-xs text-[#A5A0C8]">
                    Configure repository connection, tech stack, and team settings.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowSetupModal(false)}
                  className="h-8 w-8 rounded-xl bg-[#1E1938] text-[#A5A0C8] hover:text-white flex items-center justify-center text-xs"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleSaveSetup} className="space-y-4 text-left">
                {/* Organization Name */}
                <div>
                  <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                    Organization Workspace Name:
                  </label>
                  <input
                    type="text"
                    required
                    value={editOrgName}
                    onChange={(e) => setEditOrgName(e.target.value)}
                    placeholder="e.g. cultuss"
                    className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none"
                  />
                </div>

                {/* Git Repository Settings */}
                <div className="p-4 bg-[#0B0914] border border-[#2D264E] rounded-2xl space-y-3">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-[#8B5CF6] font-bold block">
                    Git Repository Connection
                  </span>

                  <div>
                    <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                      Repository URL:
                    </label>
                    <input
                      type="text"
                      required
                      value={editRepoUrl}
                      onChange={(e) => setEditRepoUrl(e.target.value)}
                      placeholder="https://github.com/organization/repository"
                      className="w-full bg-[#141224] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none font-mono"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                        Default Branch:
                      </label>
                      <input
                        type="text"
                        value={editBranch}
                        onChange={(e) => setEditBranch(e.target.value)}
                        placeholder="main"
                        className="w-full bg-[#141224] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none font-mono"
                      />
                    </div>

                    <div>
                      <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                        Docs / ADR Path:
                      </label>
                      <input
                        type="text"
                        value={editDocPath}
                        onChange={(e) => setEditDocPath(e.target.value)}
                        placeholder="docs/architecture"
                        className="w-full bg-[#141224] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none font-mono"
                      />
                    </div>
                  </div>
                </div>

                {/* Tech Stack Services */}
                <div className="space-y-2">
                  <label className="text-[11px] font-mono text-[#A5A0C8] block">
                    Connected Tech Stack (Selected Services):
                  </label>

                  <div className="flex flex-wrap gap-1.5 p-2 bg-[#0B0914] border border-[#2D264E] rounded-xl min-h-[38px] items-center">
                    {editTechStack.map((tech) => (
                      <span
                        key={tech}
                        className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[11px] font-mono bg-[#8B5CF6] text-white font-semibold"
                      >
                        <span>{tech}</span>
                        <button
                          type="button"
                          onClick={() => handleToggleTech(tech)}
                          className="hover:text-rose-300 transition-colors text-[10px]"
                        >
                          ✕
                        </button>
                      </span>
                    ))}

                    <input
                      type="text"
                      value={customTechInput}
                      onChange={(e) => setCustomTechInput(e.target.value)}
                      onKeyDown={handleAddCustomTech}
                      placeholder="+ Type more & Enter..."
                      className="bg-transparent border-none text-xs text-white placeholder-zinc-500 focus:outline-none flex-grow min-w-[120px] font-mono px-1 py-0.5"
                    />
                    {customTechInput.trim() && (
                      <button
                        type="button"
                        onClick={handleAddCustomTech}
                        className="px-2 py-0.5 bg-[#8B5CF6]/30 hover:bg-[#8B5CF6] text-white text-[10px] rounded-md font-mono transition-all"
                      >
                        Add +
                      </button>
                    )}
                  </div>
                </div>

                {/* Invite Teammates */}
                <div className="space-y-2">
                  <label className="text-[11px] font-mono text-[#A5A0C8] block">
                    Team Members & Invitations:
                  </label>
                  <div className="flex flex-wrap gap-1.5 p-2 bg-[#0B0914] border border-[#2D264E] rounded-xl min-h-[38px] items-center">
                    {invitedList.map((em) => (
                      <span
                        key={em}
                        className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[11px] font-mono bg-[#1E1938] border border-[#8B5CF6]/50 text-[#C4B5FD] font-semibold"
                      >
                        <span>{em}</span>
                        <button
                          type="button"
                          onClick={() => setInvitedList((prev) => prev.filter((x) => x !== em))}
                          className="hover:text-rose-400 transition-colors text-[10px]"
                        >
                          ✕
                        </button>
                      </span>
                    ))}

                    <input
                      type="email"
                      value={newInviteEmail}
                      onChange={(e) => setNewInviteEmail(e.target.value)}
                      onKeyDown={handleAddInvite}
                      placeholder="+ Add email & Enter..."
                      className="bg-transparent border-none text-xs text-white placeholder-zinc-500 focus:outline-none flex-grow min-w-[140px] font-mono px-1 py-0.5"
                    />
                    {newInviteEmail.trim() && (
                      <button
                        type="button"
                        onClick={() => handleAddInvite()}
                        className="px-2 py-0.5 bg-[#22C55E] text-white text-[10px] rounded-md font-mono font-bold transition-all"
                      >
                        + Invite
                      </button>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowSetupModal(false)}
                    className="px-4 py-2.5 bg-[#1E1938] hover:bg-[#28214B] border border-[#2D264E] text-[#A5A0C8] rounded-xl text-xs font-semibold transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-6 py-2.5 bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white font-bold text-xs rounded-xl shadow-lg shadow-[#8B5CF6]/25 transition-all"
                  >
                    Save Workspace Configuration →
                  </button>
                </div>
              </form>
            </m.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default WorkspacePage;
