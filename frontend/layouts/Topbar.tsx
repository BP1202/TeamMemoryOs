/**
 * Topbar — workspace top navigation bar.
 * Displays breadcrumb on the left and live Streak & XP Score on the right.
 */

interface TopbarProps {
  title?: string;
}

export function Topbar({ title }: TopbarProps) {
  // Read streak and XP or use standard level values
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
            <span className="text-[#C4B5FD] font-semibold">SunBots Technologies</span>
          </div>
        )}
      </div>

      {/* Global Streak & XP Score Counter */}
      <div className="flex items-center gap-3">
        {/* Streak Pill */}
        <div className="flex items-center gap-2 bg-[#1B1633] border border-[#2D264E] px-3.5 py-1.5 rounded-xl text-xs shadow-md">
          <span className="text-base">🔥</span>
          <div className="text-left font-mono">
            <span className="text-[10px] text-[#A5A0C8] block leading-none">Streak</span>
            <span className="text-xs font-bold text-amber-400 leading-tight">
              {streakDays} Days
            </span>
          </div>
        </div>

        {/* Score & XP Pill */}
        <div className="flex items-center gap-2.5 bg-[#1B1633] border border-[#2D264E] px-3.5 py-1.5 rounded-xl text-xs shadow-md">
          <div className="h-6 w-6 rounded-lg bg-[#8B5CF6]/20 border border-[#8B5CF6]/40 flex items-center justify-center text-[10px] font-bold text-[#C4B5FD] font-mono">
            L3
          </div>
          <div className="text-left font-mono">
            <span className="text-[10px] text-[#A5A0C8] block leading-none">Score</span>
            <span className="text-xs font-bold text-[#22C55E] leading-tight">
              {userXp} XP
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
