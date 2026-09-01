/**
 * Topbar — workspace top navigation bar.
 * Displays breadcrumb on the left and live Streak & XP Score on the right.
 */

import { useUIStore } from '@stores/uiStore';

interface TopbarProps {
  title?: string;
}

export function Topbar({ title }: TopbarProps) {
  const currentWorkspace = useUIStore((s) => s.currentWorkspace) || 'SunBots Technologies';
  const streakDays = 4;
  const userXp = 615;

  return (
    <header
      className="h-16 px-6 bg-[#120F24] border-b border-[#2A2447] flex items-center justify-between flex-shrink-0 z-topbar select-none"
      role="banner"
    >
      {/* Page / Context Breadcrumb */}
      <div className="flex items-center gap-3">
        {title ? (
          <h1 className="text-sm font-bold text-white tracking-tight">{title}</h1>
        ) : (
          <div className="flex items-center gap-2 text-xs text-[#A5A0C8] font-mono">
            <span>Workspace</span>
            <span>/</span>
            <span className="text-[#C4B5FD] font-semibold">{currentWorkspace}</span>
          </div>
        )}
      </div>

      {/* Global Streak & XP Score Counter */}
      <div className="flex items-center gap-2.5">
        {/* Streak Pill */}
        <div className="flex items-center gap-2 bg-[#1B1633] border border-[#2D264E] px-3 py-1.5 rounded-xl text-xs shadow-md">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
          <div className="text-left font-mono">
            <span className="text-[9px] text-[#A5A0C8] block uppercase leading-none">Streak</span>
            <span className="text-xs font-bold text-amber-400 leading-tight">
              {streakDays}d
            </span>
          </div>
        </div>

        {/* Score & XP Pill */}
        <div className="flex items-center gap-2 bg-[#1B1633] border border-[#2D264E] px-3 py-1.5 rounded-xl text-xs shadow-md">
          <span className="h-1.5 w-1.5 rounded-full bg-[#22C55E]" />
          <div className="text-left font-mono">
            <span className="text-[9px] text-[#A5A0C8] block uppercase leading-none">Score</span>
            <span className="text-xs font-bold text-[#22C55E] leading-tight">
              {userXp} XP
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
