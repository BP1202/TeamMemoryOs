import { useState } from 'react';

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
  const [members] = useState<TeamMember[]>([
    {
      name: 'Alex Vance',
      role: 'Workspace Owner',
      avatar: '👑',
      memories_created: 14,
      problems_solved: 28,
      prs_reviewed: 42,
      status: 'Active Now',
    },
    {
      name: 'Sarah Connor',
      role: 'Tech Lead',
      avatar: '🎯',
      memories_created: 38,
      problems_solved: 65,
      prs_reviewed: 112,
      status: 'Active Now',
    },
    {
      name: 'Devin Thorne (You)',
      role: 'Developer',
      avatar: '💻',
      memories_created: 22,
      problems_solved: 41,
      prs_reviewed: 19,
      status: 'Active Now',
    },
    {
      name: 'Morgan Chase',
      role: 'Security Auditor',
      avatar: '🛡️',
      memories_created: 9,
      problems_solved: 16,
      prs_reviewed: 54,
      status: 'Active 1h ago',
    },
  ]);

  const [services] = useState<ServiceCard[]>([
    {
      name: 'Auth Service',
      status: 'Healthy',
      owner: 'Sarah Connor',
      endpoints_count: 12,
      known_incidents: 3,
      memories_count: 8,
      description: 'JWT bearer validation, Bcrypt password hashing, and user authentication.',
    },
    {
      name: 'Billing & Payments',
      status: 'Healthy',
      owner: 'Alex Vance',
      endpoints_count: 8,
      known_incidents: 2,
      memories_count: 6,
      description: 'Stripe webhook listener with Redis distributed redlock execution.',
    },
    {
      name: 'Core Backend API',
      status: 'Healthy',
      owner: 'Devin Thorne',
      endpoints_count: 24,
      known_incidents: 5,
      memories_count: 14,
      description: 'FastAPI async route handlers and domain business orchestration.',
    },
    {
      name: 'PostgreSQL Database',
      status: 'Healthy',
      owner: 'Sarah Connor',
      endpoints_count: 1,
      known_incidents: 4,
      memories_count: 9,
      description: 'QueuePool connection sizing, session lifecycle, and pgvector storage.',
    },
  ]);

  return (
    <div className="min-h-screen bg-[#0B0914] text-white p-6 md:p-10 space-y-8 font-sans max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#2D264E]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono text-[#A5A0C8] uppercase tracking-wider">
              Engineering Workspace
            </span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 font-medium">
              SunBots Technologies
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <span>👥</span> Team Workspace & Services
          </h1>
          <p className="text-xs text-[#A5A0C8] mt-0.5">
            Organization overview, active engineering members, service architecture, and connected repositories.
          </p>
        </div>

        <div className="flex items-center gap-3 bg-[#141224] border border-[#2D264E] p-2.5 px-4 rounded-2xl shadow-xl">
          <span className="h-2.5 w-2.5 rounded-full bg-[#22C55E] animate-pulse" />
          <div className="text-left font-mono text-xs">
            <span className="text-white font-bold block">4 Active Engineers</span>
            <span className="text-[#A5A0C8] text-[10px]">All Services Operational</span>
          </div>
        </div>
      </div>

      {/* Workspace Health Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-[#141224] border border-[#2D264E] rounded-2xl space-y-1 shadow-lg">
          <span className="text-[10px] font-mono text-[#8B5CF6] uppercase font-bold">Team Members</span>
          <p className="text-xl font-bold text-white font-mono">4 Engineers</p>
          <p className="text-xs text-[#A5A0C8]">1 Owner, 1 Lead, 1 Dev, 1 Auditor</p>
        </div>
        <div className="p-5 bg-[#141224] border border-[#2D264E] rounded-2xl space-y-1 shadow-lg">
          <span className="text-[10px] font-mono text-[#22C55E] uppercase font-bold">Memory Coverage</span>
          <p className="text-xl font-bold text-[#22C55E] font-mono">24 Fixes Stored</p>
          <p className="text-xs text-[#A5A0C8]">Across 4 microservices</p>
        </div>
        <div className="p-5 bg-[#141224] border border-[#2D264E] rounded-2xl space-y-1 shadow-lg">
          <span className="text-[10px] font-mono text-[#22D3EE] uppercase font-bold">Weekly Savings</span>
          <p className="text-xl font-bold text-[#22D3EE] font-mono">8.5h Saved</p>
          <p className="text-xs text-[#A5A0C8]">AI resolved 6 incidents this sprint</p>
        </div>
        <div className="p-5 bg-[#141224] border border-[#2D264E] rounded-2xl space-y-1 shadow-lg">
          <span className="text-[10px] font-mono text-[#F59E0B] uppercase font-bold">Repositories Synced</span>
          <p className="text-xl font-bold text-white font-mono">3 / 3 Synced</p>
          <p className="text-xs text-[#A5A0C8]">Last synced 5 mins ago</p>
        </div>
      </div>

      {/* Engineering Team Members */}
      <div className="bg-[#141224] border border-[#2D264E] rounded-3xl p-6 shadow-xl space-y-4">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <span>👥</span> Engineering Team Members
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {members.map((m) => (
            <div key={m.name} className="p-4 bg-[#1E1938] border border-[#2D264E] rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{m.avatar}</span>
                  <div>
                    <h3 className="text-xs font-bold text-white">{m.name}</h3>
                    <p className="text-[10px] text-[#A5A0C8] font-mono">{m.role}</p>
                  </div>
                </div>
                <span className="h-2 w-2 rounded-full bg-[#22C55E]" />
              </div>

              <div className="grid grid-cols-3 gap-1 text-center pt-2 border-t border-[#2D264E] text-[10px] font-mono">
                <div>
                  <span className="text-[#8B5CF6] font-bold block">{m.memories_created}</span>
                  <span className="text-[#A5A0C8]">Saved</span>
                </div>
                <div>
                  <span className="text-[#22C55E] font-bold block">{m.problems_solved}</span>
                  <span className="text-[#A5A0C8]">Solved</span>
                </div>
                <div>
                  <span className="text-[#22D3EE] font-bold block">{m.prs_reviewed}</span>
                  <span className="text-[#A5A0C8]">PRs</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Service Explorer */}
      <div className="bg-[#141224] border border-[#2D264E] rounded-3xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-[#2D264E]">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span>📦</span> Service Architecture Catalog
            </h2>
            <p className="text-xs text-[#A5A0C8]">
              Microservices connected to TeamMemoryOS institutional memory
            </p>
          </div>
          <span className="text-xs font-mono text-[#22C55E] bg-[#22C55E]/15 border border-[#22C55E]/30 px-3 py-1 rounded-full font-bold">
            4 / 4 Healthy
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {services.map((svc) => (
            <div key={svc.name} className="p-5 bg-[#1E1938] border border-[#2D264E] rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-[#22C55E]" />
                  <h3 className="text-sm font-bold text-white">{svc.name}</h3>
                </div>
                <span className="text-[10px] font-mono text-[#A5A0C8]">Owner: {svc.owner}</span>
              </div>

              <p className="text-xs text-zinc-300 leading-relaxed">{svc.description}</p>

              <div className="flex items-center gap-4 text-[11px] font-mono text-[#A5A0C8] pt-2 border-t border-[#2D264E]">
                <span>{svc.endpoints_count} Endpoints</span>
                <span>•</span>
                <span className="text-[#22D3EE]">{svc.memories_count} Stored Fixes</span>
                <span>•</span>
                <span className="text-[#22C55E]">{svc.known_incidents} Past Incidents</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
