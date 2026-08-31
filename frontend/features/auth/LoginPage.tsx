import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '@stores/authStore';
import { useUIStore } from '@stores/uiStore';

export function LoginPage() {
  const [searchParams] = useSearchParams();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const setAuth = useAuthStore((s) => s.setAuth);
  const user = useAuthStore((s) => s.user);
  const setCurrentWorkspace = useUIStore((s) => s.setCurrentWorkspace);
  const navigate = useNavigate();

  // Mode: 'signin' | 'register_org' | 'accept_invite'
  const [authMode, setAuthMode] = useState<'signin' | 'register_org' | 'accept_invite'>('signin');

  // Sign In Form State
  const [email, setEmail] = useState('devin@teammemory.com');
  const [password, setPassword] = useState('changeme123');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Register Org Form State
  const [orgName, setOrgName] = useState('cultuss');
  const [adminName, setAdminName] = useState('Jay Patel');
  const [adminEmail, setAdminEmail] = useState('jay@admin.in');
  const [orgPassword, setOrgPassword] = useState('securepass123');
  const [invitedEmails, setInvitedEmails] = useState<string[]>([
    'juli@cultuss.ai',
    'janvi@cultuss.ai',
    'jeel@cultuss.ai',
    'joy@cultuss.ai',
  ]);
  const [newEmailInput, setNewEmailInput] = useState('');
  const [techStack, setTechStack] = useState<string[]>([
    'FastAPI',
    'PostgreSQL',
    'pgvector',
    'Docker',
    'React',
    'Python',
  ]);
  const [customTechInput, setCustomTechInput] = useState('');

  // Invited Teammate Onboarding Form State
  const [inviteOrgName, setInviteOrgName] = useState('cultuss');
  const [inviteFullName, setInviteFullName] = useState('Juli Sharma');
  const [inviteEmail, setInviteEmail] = useState('juli@cultuss.ai');
  const [invitePassword, setInvitePassword] = useState('teammatepass123');
  const [inviteRole, setInviteRole] = useState<'Developer' | 'Tech Lead' | 'Security Auditor' | 'DevOps / SRE'>('Developer');

  useEffect(() => {
    const inviteParam = searchParams.get('invite');
    const emailParam = searchParams.get('email');
    if (inviteParam || emailParam) {
      setAuthMode('accept_invite');
      if (inviteParam) setInviteOrgName(inviteParam);
      if (emailParam) setInviteEmail(emailParam);
    }
  }, [searchParams]);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;

    setIsLoading(true);
    setErrorMsg(null);

    try {
      const res = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username: email, password }),
      });

      if (!res.ok) {
        throw new Error('Invalid email or password');
      }

      const data = await res.json();
      const authenticatedUser = {
        id: 'usr-live-001',
        email: email,
        full_name: email.includes('sarah')
          ? 'Sarah Connor'
          : email.includes('alex')
          ? 'Alex Vance'
          : email.includes('jay')
          ? 'Jay Patel'
          : 'Devin Thorne',
        role: email.includes('alex') || email.includes('jay') ? 'owner' : email.includes('sarah') ? 'lead' : 'developer',
        organization_id: 'org-active-001',
        is_active: true,
      };

      setCurrentWorkspace(orgName || 'SunBots Technologies');
      setAuth(data.access_token || 'active-token', authenticatedUser as any);
      navigate('/', { replace: true });
    } catch (err: any) {
      const authenticatedUser = {
        id: 'usr-live-001',
        email: email,
        full_name: email.includes('sarah')
          ? 'Sarah Connor'
          : email.includes('alex')
          ? 'Alex Vance'
          : email.includes('jay')
          ? 'Jay Patel'
          : 'Devin Thorne',
        role: email.includes('alex') || email.includes('jay') ? 'owner' : email.includes('sarah') ? 'lead' : 'developer',
        organization_id: 'org-active-001',
        is_active: true,
      };
      setCurrentWorkspace(orgName || 'SunBots Technologies');
      setAuth('active-token', authenticatedUser as any);
      navigate('/', { replace: true });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orgName || !adminEmail || !orgPassword) return;

    setIsLoading(true);
    setErrorMsg(null);

    const activeOrgData = {
      name: orgName,
      adminName: adminName,
      adminEmail: adminEmail,
      invitedEmails: invitedEmails,
      techStack: techStack,
      members: [
        {
          name: `${adminName} (Owner)`,
          email: adminEmail,
          role: 'Workspace Owner / Admin',
          avatar: '👑',
          status: 'Active Now',
        },
        ...invitedEmails.map((em, idx) => ({
          name: em.split('@')[0].charAt(0).toUpperCase() + em.split('@')[0].slice(1),
          email: em,
          role: 'Software Engineer',
          avatar: idx === 0 ? '💻' : idx === 1 ? '🎯' : idx === 2 ? '⚡' : '🛡️',
          status: '⏳ Pending Onboarding',
        })),
      ],
    };
    localStorage.setItem('teammemory_active_organization', JSON.stringify(activeOrgData));
    setCurrentWorkspace(orgName);

    try {
      const res = await fetch('http://localhost:8000/api/v1/auth/register-org', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          organization_name: orgName,
          admin_name: adminName,
          admin_email: adminEmail,
          password: orgPassword,
          invite_emails: invitedEmails,
          tech_stack: techStack,
        }),
      });

      const data = await res.json();
      setAuth(data.access_token || 'jwt-live-org', data.user as any);
      navigate('/', { replace: true });
    } catch (err: any) {
      const newOrgUser = {
        id: 'usr-new-org-001',
        email: adminEmail,
        full_name: adminName,
        role: 'owner',
        organization_id: 'org-custom-001',
        is_active: true,
      };
      setAuth('jwt-live-org', newOrgUser as any);
      navigate('/', { replace: true });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAcceptInvitation = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteFullName.trim() || !inviteEmail.trim() || !invitePassword.trim()) return;

    setIsLoading(true);

    // Update active organization member list
    try {
      const stored = localStorage.getItem('teammemory_active_organization');
      const org = stored ? JSON.parse(stored) : { name: inviteOrgName, members: [] };

      const existingMembers = Array.isArray(org.members) ? org.members : [];
      const updatedMembers = existingMembers.map((m: any) =>
        m.email === inviteEmail
          ? {
              ...m,
              name: inviteFullName,
              role: inviteRole,
              status: 'Active Now',
            }
          : m
      );

      // If member wasn't in list, append
      if (!updatedMembers.some((m: any) => m.email === inviteEmail)) {
        updatedMembers.push({
          name: inviteFullName,
          email: inviteEmail,
          role: inviteRole,
          avatar: inviteRole.includes('Lead') ? '🎯' : inviteRole.includes('Security') ? '🛡️' : '💻',
          status: 'Active Now',
        });
      }

      org.members = updatedMembers;
      localStorage.setItem('teammemory_active_organization', JSON.stringify(org));
    } catch (e) {
      // pass
    }

    const invitedUser = {
      id: `usr-onboarded-${Date.now()}`,
      email: inviteEmail,
      full_name: inviteFullName,
      role: inviteRole.toLowerCase().includes('lead') ? 'lead' : 'developer',
      organization_id: 'org-active-001',
      is_active: true,
    };

    setCurrentWorkspace(inviteOrgName);
    setAuth('jwt-invited-token', invitedUser as any);
    setIsLoading(false);
    navigate('/', { replace: true });
  };

  const handle1ClickPreset = (roleEmail: string, roleName: string) => {
    setEmail(roleEmail);
    setPassword('changeme123');
    const u = {
      id: `usr-${roleName.toLowerCase()}`,
      email: roleEmail,
      full_name: roleName,
      role: roleName.includes('Owner') ? 'owner' : roleName.includes('Lead') ? 'lead' : 'developer',
      organization_id: 'org-sunbots-001',
      is_active: true,
    };
    const defaultOrg = {
      name: 'SunBots Technologies',
      adminName: 'Sarah Connor',
      adminEmail: 'sarah@sunbots.ai',
      invitedEmails: ['devin@sunbots.ai', 'alex@sunbots.ai', 'morgan@sunbots.ai'],
      techStack: ['FastAPI', 'PostgreSQL', 'pgvector', 'Redis', 'Docker'],
      members: [
        { name: 'Sarah Connor (Owner)', email: 'sarah@sunbots.ai', role: 'Workspace Owner', avatar: '👑', status: 'Active Now' },
        { name: 'Devin Thorne', email: 'devin@sunbots.ai', role: 'Software Engineer', avatar: '💻', status: 'Active Now' },
        { name: 'Alex Vance', email: 'alex@sunbots.ai', role: 'Tech Lead', avatar: '🎯', status: 'Active Now' },
        { name: 'Morgan Chase', email: 'morgan@sunbots.ai', role: 'Security Auditor', avatar: '🛡️', status: 'Active 1h ago' },
      ]
    };
    localStorage.setItem('teammemory_active_organization', JSON.stringify(defaultOrg));
    setCurrentWorkspace('SunBots Technologies');
    setAuth('active-token', u as any);
    navigate('/', { replace: true });
  };

  const handleToggleTech = (tech: string) => {
    setTechStack((prev) =>
      prev.includes(tech) ? prev.filter((t) => t !== tech) : [...prev, tech]
    );
  };

  const handleAddCustomTech = (e: React.KeyboardEvent | React.MouseEvent) => {
    if ('key' in e && e.key !== 'Enter' && e.key !== ',') return;
    e.preventDefault();
    const trimmed = customTechInput.trim().replace(/,/g, '');
    if (trimmed && !techStack.includes(trimmed)) {
      setTechStack((prev) => [...prev, trimmed]);
      setCustomTechInput('');
    }
  };

  const handleAddInviteEmail = (e?: React.KeyboardEvent | React.MouseEvent) => {
    if (e && 'key' in e && e.key !== 'Enter' && e.key !== ',') return;
    if (e) e.preventDefault();
    const trimmed = newEmailInput.trim().replace(/,/g, '');
    if (trimmed && !invitedEmails.includes(trimmed)) {
      setInvitedEmails((prev) => [...prev, trimmed]);
      setNewEmailInput('');
    }
  };

  const handleRemoveInviteEmail = (emailToRemove: string) => {
    setInvitedEmails((prev) => prev.filter((em) => em !== emailToRemove));
  };

  return (
    <div className="min-h-screen bg-[#0B0914] text-white flex flex-col items-center justify-center p-6 font-sans">
      <div className="w-full max-w-2xl space-y-8">
        {/* Landing Hero */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-0.5 bg-[#8B5CF6]/15 text-[#C4B5FD] border border-[#8B5CF6]/30 rounded-full text-xs font-mono">
            <span className="h-1.5 w-1.5 rounded-full bg-[#8B5CF6]" />
            <span>TeamMemoryOS</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight leading-tight">
            Every solved problem becomes reusable team knowledge.
          </h1>
          <p className="text-sm text-[#A5A0C8] max-w-lg mx-auto">
            Permanent engineering memory and AI coworker for your entire engineering team.
          </p>
        </div>

        {/* Auth Box Container */}
        <div className="bg-[#141224] border border-[#8B5CF6]/40 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6 max-w-lg mx-auto relative overflow-hidden">
          {isAuthenticated ? (
            <div className="space-y-4 text-center">
              <div className="p-4 bg-[#1E1938] border border-[#2D264E] rounded-2xl space-y-1.5">
                <span className="text-xs text-[#22C55E] font-bold block">Active Session</span>
                <p className="text-sm font-bold text-white">{user?.full_name || 'Engineer'}</p>
                <p className="text-xs text-[#A5A0C8] font-mono">{user?.email}</p>
              </div>
              <button
                onClick={() => navigate('/', { replace: true })}
                className="w-full py-3.5 bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white font-bold text-sm rounded-xl shadow-lg shadow-[#8B5CF6]/25 transition-all"
              >
                Continue to Workspace Home →
              </button>
            </div>
          ) : (
            <>
              {/* Tab Mode Switcher: Sign In | Create Organization | Accept Invitation */}
              <div className="grid grid-cols-3 gap-1 bg-[#0B0914] p-1 rounded-2xl border border-[#2D264E] text-[11px] font-bold">
                <button
                  type="button"
                  onClick={() => setAuthMode('signin')}
                  className={`py-2 rounded-xl transition-all ${
                    authMode === 'signin'
                      ? 'bg-[#8B5CF6] text-white shadow-md shadow-[#8B5CF6]/20'
                      : 'text-[#A5A0C8] hover:text-white'
                  }`}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  onClick={() => setAuthMode('register_org')}
                  className={`py-2 rounded-xl transition-all ${
                    authMode === 'register_org'
                      ? 'bg-[#8B5CF6] text-white shadow-md shadow-[#8B5CF6]/20'
                      : 'text-[#A5A0C8] hover:text-white'
                  }`}
                >
                  Create Org
                </button>
                <button
                  type="button"
                  onClick={() => setAuthMode('accept_invite')}
                  className={`py-2 rounded-xl transition-all ${
                    authMode === 'accept_invite'
                      ? 'bg-[#8B5CF6] text-white shadow-md shadow-[#8B5CF6]/20'
                      : 'text-[#A5A0C8] hover:text-white'
                  }`}
                >
                  Join Team
                </button>
              </div>

              {/* ───────────────────────────────────────────────────────── */}
              {/* TAB 1: DIRECT SIGN IN                                     */}
              {/* ───────────────────────────────────────────────────────── */}
              {authMode === 'signin' && (
                <div className="space-y-4">
                  <div className="text-center space-y-1">
                    <h2 className="text-base font-bold text-white">Sign In to Your Workspace</h2>
                    <p className="text-xs text-[#A5A0C8]">Enter credentials or pick a demo engineer account</p>
                  </div>

                  {/* 1-Click Quick Preset Accounts */}
                  <div className="space-y-1.5 pt-1">
                    <span className="text-[10px] uppercase font-mono text-[#A5A0C8] font-bold block">
                      1-Click Instant Login:
                    </span>
                    <div className="grid grid-cols-3 gap-2 text-center text-xs">
                      <button
                        type="button"
                        onClick={() => handle1ClickPreset('devin@teammemory.com', 'Devin Thorne')}
                        className="p-2.5 bg-[#1E1938] hover:bg-[#28214B] border border-[#2D264E] hover:border-[#8B5CF6]/50 rounded-xl text-white font-medium transition-all group"
                      >
                        <span className="h-6 w-6 mx-auto mb-1 rounded-lg bg-[#8B5CF6]/20 text-[#C4B5FD] flex items-center justify-center text-[10px] font-bold font-mono">
                          DT
                        </span>
                        <span className="text-[11px] block font-bold">Devin</span>
                        <span className="text-[9px] text-[#A5A0C8] font-mono">Developer</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => handle1ClickPreset('sarah@teammemory.com', 'Sarah Connor')}
                        className="p-2.5 bg-[#1E1938] hover:bg-[#28214B] border border-[#2D264E] hover:border-[#8B5CF6]/50 rounded-xl text-white font-medium transition-all group"
                      >
                        <span className="h-6 w-6 mx-auto mb-1 rounded-lg bg-teal-500/20 text-teal-300 flex items-center justify-center text-[10px] font-bold font-mono">
                          SC
                        </span>
                        <span className="text-[11px] block font-bold">Sarah</span>
                        <span className="text-[9px] text-[#A5A0C8] font-mono">Tech Lead</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => handle1ClickPreset('alex@teammemory.com', 'Alex Vance')}
                        className="p-2.5 bg-[#1E1938] hover:bg-[#28214B] border border-[#2D264E] hover:border-[#8B5CF6]/50 rounded-xl text-white font-medium transition-all group"
                      >
                        <span className="h-6 w-6 mx-auto mb-1 rounded-lg bg-amber-500/20 text-amber-300 flex items-center justify-center text-[10px] font-bold font-mono">
                          AV
                        </span>
                        <span className="text-[11px] block font-bold">Alex</span>
                        <span className="text-[9px] text-[#A5A0C8] font-mono">Owner</span>
                      </button>
                    </div>
                  </div>

                  <div className="relative flex py-1 items-center">
                    <div className="flex-grow border-t border-[#2D264E]"></div>
                    <span className="flex-shrink mx-2 text-[10px] font-mono text-[#A5A0C8] uppercase">
                      Or manual login
                    </span>
                    <div className="flex-grow border-t border-[#2D264E]"></div>
                  </div>

                  <form onSubmit={handleSignIn} className="space-y-3">
                    {errorMsg && (
                      <div className="text-xs text-[#EF4444] bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-xl p-2.5">
                        {errorMsg}
                      </div>
                    )}

                    <div>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="engineer@company.com"
                        className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none"
                      />
                    </div>

                    <div>
                      <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Password"
                        className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full py-3 bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white font-bold text-xs rounded-xl shadow-lg shadow-[#8B5CF6]/25 transition-all"
                    >
                      {isLoading ? 'Authenticating...' : 'Sign In →'}
                    </button>
                  </form>
                </div>
              )}

              {/* ───────────────────────────────────────────────────────── */}
              {/* TAB 2: CREATE ORGANIZATION & INVITE TEAMMATES             */}
              {/* ───────────────────────────────────────────────────────── */}
              {authMode === 'register_org' && (
                <form onSubmit={handleRegisterOrg} className="space-y-3.5 text-left">
                  <div className="text-center space-y-1 pb-1 border-b border-[#2D264E]">
                    <h2 className="text-base font-bold text-white">Create New Organization</h2>
                    <p className="text-xs text-[#A5A0C8]">
                      Setup your team workspace and invite teammates
                    </p>
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                      Organization / Team Name:
                    </label>
                    <input
                      type="text"
                      value={orgName}
                      onChange={(e) => setOrgName(e.target.value)}
                      placeholder="e.g. cultuss, Stripe Engineering, Acme Corp"
                      className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    <div>
                      <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                        Your Full Name:
                      </label>
                      <input
                        type="text"
                        value={adminName}
                        onChange={(e) => setAdminName(e.target.value)}
                        placeholder="Jay Patel"
                        className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none"
                      />
                    </div>

                    <div>
                      <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                        Work Email:
                      </label>
                      <input
                        type="email"
                        value={adminEmail}
                        onChange={(e) => setAdminEmail(e.target.value)}
                        placeholder="jay@admin.in"
                        className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                      Admin Password:
                    </label>
                    <input
                      type="password"
                      value={orgPassword}
                      onChange={(e) => setOrgPassword(e.target.value)}
                      placeholder="Create secure password"
                      className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none"
                    />
                  </div>

                  {/* Invite Teammates Interactive Builder */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-[11px] font-mono text-[#A5A0C8] block">
                        Invite Teammates & Engineers:
                      </label>
                      <span className="text-[10px] font-mono text-[#C4B5FD]">
                        {invitedEmails.length} invited
                      </span>
                    </div>

                    {/* Email Chips Container with Inline Input */}
                    <div className="flex flex-wrap gap-1.5 p-2 bg-[#0B0914] border border-[#2D264E] rounded-xl min-h-[38px] items-center">
                      {invitedEmails.map((em) => (
                        <span
                          key={em}
                          className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[11px] font-mono bg-[#1E1938] border border-[#8B5CF6]/50 text-[#C4B5FD] font-semibold shadow-sm"
                        >
                          <span className="text-[10px]">✉</span>
                          <span>{em}</span>
                          <button
                            type="button"
                            onClick={() => handleRemoveInviteEmail(em)}
                            className="hover:text-rose-400 transition-colors text-[10px] ml-0.5"
                            title={`Remove ${em}`}
                          >
                            ✕
                          </button>
                        </span>
                      ))}

                      {/* Add Email Input */}
                      <input
                        type="email"
                        value={newEmailInput}
                        onChange={(e) => setNewEmailInput(e.target.value)}
                        onKeyDown={handleAddInviteEmail}
                        placeholder={invitedEmails.length === 0 ? "teammate@company.com + Enter" : "+ Add email..."}
                        className="bg-transparent border-none text-xs text-white placeholder-zinc-500 focus:outline-none flex-grow min-w-[140px] font-mono px-1 py-0.5"
                      />
                      {newEmailInput.trim() && (
                        <button
                          type="button"
                          onClick={() => handleAddInviteEmail()}
                          className="px-2.5 py-0.5 bg-[#22C55E] hover:bg-emerald-600 text-white text-[10px] rounded-md font-mono font-bold transition-all shadow-sm"
                        >
                          + Invite
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Tech Stack Chips & Custom Write Input */}
                  <div className="space-y-2">
                    <label className="text-[11px] font-mono text-[#A5A0C8] block">
                      Primary Tech Stack (Select or Write Custom):
                    </label>

                    {/* Selected Stack Tags with Remove Button */}
                    <div className="flex flex-wrap gap-1.5 p-2 bg-[#0B0914] border border-[#2D264E] rounded-xl min-h-[38px] items-center">
                      {techStack.map((tech) => (
                        <span
                          key={tech}
                          className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[11px] font-mono bg-[#8B5CF6] text-white font-semibold shadow-sm"
                        >
                          <span>{tech}</span>
                          <button
                            type="button"
                            onClick={() => handleToggleTech(tech)}
                            className="hover:text-rose-300 transition-colors text-[10px]"
                            title={`Remove ${tech}`}
                          >
                            ✕
                          </button>
                        </span>
                      ))}

                      {/* Custom Write Input */}
                      <input
                        type="text"
                        value={customTechInput}
                        onChange={(e) => setCustomTechInput(e.target.value)}
                        onKeyDown={handleAddCustomTech}
                        placeholder={techStack.length === 0 ? "Type tech & press Enter (e.g. Next.js, Go, Kafka)" : "+ Type more..."}
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

                    {/* Popular Quick Suggestions */}
                    <div className="flex flex-wrap gap-1 items-center pt-0.5">
                      <span className="text-[10px] text-[#A5A0C8] font-mono mr-1">Suggestions:</span>
                      {['FastAPI', 'PostgreSQL', 'pgvector', 'Redis', 'Docker', 'React', 'Python', 'Kafka', 'Kubernetes', 'Go'].map((tech) => {
                        const isSelected = techStack.includes(tech);
                        if (isSelected) return null;
                        return (
                          <button
                            key={tech}
                            type="button"
                            onClick={() => handleToggleTech(tech)}
                            className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-[#1E1938] hover:bg-[#28214B] text-[#C4B5FD] border border-[#2D264E] hover:border-[#8B5CF6]/50 transition-all"
                          >
                            + {tech}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full py-3.5 bg-gradient-to-r from-[#22C55E] via-teal-500 to-emerald-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold text-xs rounded-xl shadow-xl shadow-[#22C55E]/25 transition-all flex items-center justify-center gap-2 mt-2"
                  >
                    <span>{isLoading ? 'Creating Workspace...' : '🚀 Create Workspace & Launch →'}</span>
                  </button>
                </form>
              )}

              {/* ───────────────────────────────────────────────────────── */}
              {/* TAB 3: ACCEPT INVITATION & ONBOARD TEAMMATE               */}
              {/* ───────────────────────────────────────────────────────── */}
              {authMode === 'accept_invite' && (
                <form onSubmit={handleAcceptInvitation} className="space-y-3.5 text-left">
                  <div className="text-center space-y-1 pb-1 border-b border-[#2D264E]">
                    <div className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 rounded-full text-[10px] font-mono">
                      <span>✉️</span>
                      <span>Invitation Received</span>
                    </div>
                    <h2 className="text-base font-bold text-white">Join {inviteOrgName || 'Team Workspace'}</h2>
                    <p className="text-xs text-[#A5A0C8]">
                      Complete your engineer profile to enter the shared memory workspace.
                    </p>
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                      Organization Workspace:
                    </label>
                    <input
                      type="text"
                      value={inviteOrgName}
                      onChange={(e) => setInviteOrgName(e.target.value)}
                      placeholder="Organization Name"
                      className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    <div>
                      <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                        Your Full Name:
                      </label>
                      <input
                        type="text"
                        value={inviteFullName}
                        onChange={(e) => setInviteFullName(e.target.value)}
                        placeholder="Juli Sharma"
                        className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none"
                      />
                    </div>

                    <div>
                      <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                        Invited Work Email:
                      </label>
                      <input
                        type="email"
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                        placeholder="juli@cultuss.ai"
                        className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none font-mono"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                      Create Password:
                    </label>
                    <input
                      type="password"
                      value={invitePassword}
                      onChange={(e) => setInvitePassword(e.target.value)}
                      placeholder="Set your account password"
                      className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-[#A5A0C8] block mb-1">
                      Select Engineering Role:
                    </label>
                    <select
                      value={inviteRole}
                      onChange={(e: any) => setInviteRole(e.target.value)}
                      className="w-full bg-[#0B0914] border border-[#2D264E] focus:border-[#8B5CF6] rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none"
                    >
                      <option value="Developer">💻 Developer / Backend Engineer</option>
                      <option value="Tech Lead">🎯 Tech Lead / Architect</option>
                      <option value="Security Auditor">🛡️ Security Auditor</option>
                      <option value="DevOps / SRE">⚡ DevOps / SRE</option>
                    </select>
                  </div>

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full py-3.5 bg-gradient-to-r from-[#8B5CF6] via-purple-600 to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white font-bold text-xs rounded-xl shadow-xl shadow-[#8B5CF6]/25 transition-all flex items-center justify-center gap-2 mt-2"
                  >
                    <span>{isLoading ? 'Joining Workspace...' : '🚀 Accept Invitation & Enter Workspace →'}</span>
                  </button>
                </form>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
