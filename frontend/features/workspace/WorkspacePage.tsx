import { useState } from 'react';
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

export function WorkspacePage() {
  const currentWorkspace = useUIStore((s) => s.currentWorkspace);
  const user = useAuthStore((s) => s.user);

  // Read active organization metadata
  const [activeOrg] = useState(() => {
    try {
      const stored = localStorage.getItem('teammemory_active_organization');
      if (stored) return JSON.parse(stored);
    } catch (e) {
      // pass
    }
    return {
      name: currentWorkspace || 'SunBots Technologies',
      adminName: user?.full_name || 'Sarah Connor',
      adminEmail: user?.email || 'sarah@sunbots.ai',
      invitedEmails: ['devin@sunbots.ai', 'alex@sunbots.ai', 'morgan@sunbots.ai'],
      techStack: ['FastAPI', 'PostgreSQL', 'pgvector', 'Redis', 'Docker'],
    };
  });

  // Dynamic Members Roster
  const [members] = useState<TeamMember[]>(() => {
    if (Array.isArray(activeOrg.members) && activeOrg.members.length > 0) {
      return activeOrg.members.map((m: any, idx: number) => ({
        name: m.name,
        role: m.role || 'Software Engineer',
        avatar: m.avatar || (m.role?.includes('Owner') ? '👑' : idx % 3 === 0 ? '💻' : idx % 3 === 1 ? '🎯' : '🛡️'),
        memories_created: m.status?.includes('Pending') ? 0 : 8 + idx * 4,
        problems_solved: m.status?.includes('Pending') ? 0 : 12 + idx * 6,
        prs_reviewed: m.status?.includes('Pending') ? 0 : 15 + idx * 8,
        status: m.status || 'Active Now',
      }));
    }

    const list: TeamMember[] = [
      {
        name: `${activeOrg.adminName || 'Admin'} (Owner)`,
        role: 'Workspace Owner / Lead',
        avatar: '👑',
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
          avatar: idx === 0 ? '💻' : idx === 1 ? '🎯' : '🛡️',
          memories_created: 8 + idx * 4,
          problems_solved: 12 + idx * 6,
          prs_reviewed: 15 + idx * 8,
          status: 'Active Now',
        });
      });
    }

    return list;
  });

  // Dynamic Services Catalog from Organization Tech Stack
  const [services] = useState<ServiceCard[]>(() => {
    const stack = Array.isArray(activeOrg.techStack) && activeOrg.techStack.length > 0
      ? activeOrg.techStack
      : ['FastAPI', 'PostgreSQL', 'pgvector', 'Redis', 'Docker'];

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
        owner: activeOrg.adminName || 'Sarah Connor',
        endpoints_count: 6 + idx * 4,
        known_incidents: 2 + (idx % 3),
        memories_count: 5 + idx * 3,
        description: desc,
      };
    });
  });

  return (
    <div className="min-h-screen bg-[#0B0914] text-white p-6 md:p-10 space-y-8 font-sans max-w-7xl mx-auto">
      {/* Header */}
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
          <div className="p-3 px-4 bg-[#141224] border border-[#2D264E] rounded-2xl flex items-center gap-4 text-xs font-mono">
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
                    {m.name.replace(/[^a-zA-Z]/g, '').slice(0, 2).toUpperCase() || 'EN'}
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
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <span>⚙️</span> Connected Services & Primary Tech Stack
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
    </div>
  );
}

export default WorkspacePage;
