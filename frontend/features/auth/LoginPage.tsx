import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@stores/authStore';

export function LoginPage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const setAuth = useAuthStore((s) => s.setAuth);
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();

  // Mode: 'signin' | 'register_org' | 'demo'
  const [authMode, setAuthMode] = useState<'signin' | 'register_org' | 'demo'>('signin');

  // Sign In Form State
  const [email, setEmail] = useState('devin@teammemory.com');
  const [password, setPassword] = useState('changeme123');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Register Org Form State
  const [orgName, setOrgName] = useState('SunBots Technologies');
  const [adminName, setAdminName] = useState('Sarah Connor');
  const [adminEmail, setAdminEmail] = useState('sarah@sunbots.ai');
  const [orgPassword, setOrgPassword] = useState('securepass123');
  const [invitedEmails, setInvitedEmails] = useState<string[]>([
    'devin@sunbots.ai',
    'alex@sunbots.ai',
    'morgan@sunbots.ai',
  ]);
  const [newEmailInput, setNewEmailInput] = useState('');
  const [techStack, setTechStack] = useState<string[]>(['FastAPI', 'PostgreSQL', 'pgvector', 'Docker']);

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
          : 'Devin Thorne',
        role: email.includes('alex') ? 'owner' : email.includes('sarah') ? 'lead' : 'developer',
        organization_id: 'org-sunbots-001',
        is_active: true,
      };

      setAuth(data.access_token || 'active-token', authenticatedUser as any);
      navigate('/', { replace: true });
    } catch (err: any) {
      // Fallback local auth for instant testing
      const authenticatedUser = {
        id: 'usr-live-001',
        email: email,
        full_name: email.includes('sarah')
          ? 'Sarah Connor'
          : email.includes('alex')
          ? 'Alex Vance'
          : 'Devin Thorne',
        role: email.includes('alex') ? 'owner' : email.includes('sarah') ? 'lead' : 'developer',
        organization_id: 'org-sunbots-001',
        is_active: true,
      };
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
    setAuth('active-token', u as any);
    navigate('/', { replace: true });
  };

  const [customTechInput, setCustomTechInput] = useState('');

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
          <div className="inline-flex items-center gap-2 px-3.5 py-1 bg-[#8B5CF6]/15 text-[#C4B5FD] border border-[#8B5CF6]/30 rounded-full text-xs font-mono">
            <span>🧠</span>
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
                <span className="text-xs text-[#22C55E] font-bold block">✓ Active Session</span>
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
              {/* Tab Mode Switcher: Sign In | Create Organization */}
              <div className="grid grid-cols-2 gap-1 bg-[#0B0914] p-1 rounded-2xl border border-[#2D264E] text-xs font-bold">
                <button
                  type="button"
                  onClick={() => setAuthMode('signin')}
                  className={`py-2.5 rounded-xl transition-all ${
                    authMode === 'signin'
                      ? 'bg-[#8B5CF6] text-white shadow-md shadow-[#8B5CF6]/20'
                      : 'text-[#A5A0C8] hover:text-white'
                  }`}
                >
                  🔑 Sign In
                </button>
                <button
                  type="button"
                  onClick={() => setAuthMode('register_org')}
                  className={`py-2.5 rounded-xl transition-all ${
                    authMode === 'register_org'
                      ? 'bg-[#8B5CF6] text-white shadow-md shadow-[#8B5CF6]/20'
                      : 'text-[#A5A0C8] hover:text-white'
                  }`}
                >
                  🏢 Create Organization
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
                        <span className="text-base block mb-0.5">💻</span>
                        <span className="text-[11px] block font-bold">Devin</span>
                        <span className="text-[9px] text-[#A5A0C8] font-mono">Developer</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => handle1ClickPreset('sarah@teammemory.com', 'Sarah Connor')}
                        className="p-2.5 bg-[#1E1938] hover:bg-[#28214B] border border-[#2D264E] hover:border-[#8B5CF6]/50 rounded-xl text-white font-medium transition-all group"
                      >
                        <span className="text-base block mb-0.5">🎯</span>
                        <span className="text-[11px] block font-bold">Sarah</span>
                        <span className="text-[9px] text-[#A5A0C8] font-mono">Tech Lead</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => handle1ClickPreset('alex@teammemory.com', 'Alex Vance')}
                        className="p-2.5 bg-[#1E1938] hover:bg-[#28214B] border border-[#2D264E] hover:border-[#8B5CF6]/50 rounded-xl text-white font-medium transition-all group"
                      >
                        <span className="text-base block mb-0.5">👑</span>
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
                      placeholder="e.g. SunBots Technologies, Acme Corp"
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
                        placeholder="Sarah Connor"
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
                        placeholder="sarah@sunbots.ai"
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
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
