import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from '@components/ui/Dialog';
import { UtilityIcons } from '@config/icons';

interface CommandItem {
  id: string;
  title: string;
  category: string;
  action: () => void;
  icon: string;
}

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const commands: CommandItem[] = [
    {
      id: 'nav-home',
      title: 'Go to Memory Home',
      category: 'Navigation',
      action: () => {
        navigate('/');
        setOpen(false);
      },
      icon: '🏠',
    },
    {
      id: 'nav-ai',
      title: 'Ask AI Assistant',
      category: 'Navigation',
      action: () => {
        navigate('/chat');
        setOpen(false);
      },
      icon: '🤖',
    },
    {
      id: 'nav-book',
      title: 'Open Memory Book',
      category: 'Navigation',
      action: () => {
        navigate('/knowledge');
        setOpen(false);
      },
      icon: '📖',
    },
    {
      id: 'nav-incidents',
      title: 'Open Incident Investigator',
      category: 'Navigation',
      action: () => {
        navigate('/incidents');
        setOpen(false);
      },
      icon: '🚨',
    },
    {
      id: 'nav-workspace',
      title: 'Workspace & Services',
      category: 'Navigation',
      action: () => {
        navigate('/workspace');
        setOpen(false);
      },
      icon: '👥',
    },
    {
      id: 'mem-postgres',
      title: 'PostgreSQL Connection Limit Exceeded (Pool Fix)',
      category: 'Verified Memory',
      action: () => {
        navigate('/knowledge');
        setOpen(false);
      },
      icon: '📦',
    },
    {
      id: 'mem-jwt',
      title: 'JWT Token Validation 401 Signature Fix',
      category: 'Verified Memory',
      action: () => {
        navigate('/knowledge');
        setOpen(false);
      },
      icon: '🔐',
    },
    {
      id: 'mem-redis',
      title: 'Redis Distributed Redlock Concurrency Fix',
      category: 'Verified Memory',
      action: () => {
        navigate('/knowledge');
        setOpen(false);
      },
      icon: '⚡',
    },
  ];

  const filtered = commands.filter(
    (c) =>
      c.title.toLowerCase().includes(query.toLowerCase()) ||
      c.category.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="max-w-xl p-0 overflow-hidden bg-[#141224] border border-[#8B5CF6]/40 text-white rounded-3xl shadow-2xl">
        <div className="sr-only">
          <DialogTitle>Command palette</DialogTitle>
        </div>

        {/* Search input */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-[#2D264E] bg-[#1E1938]">
          <UtilityIcons.Search className="h-5 w-5 text-[#8B5CF6] flex-shrink-0" aria-hidden="true" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command, memory, or page name..."
            className="flex-1 bg-transparent text-sm text-white placeholder-zinc-500 outline-none"
            autoFocus
          />
          <kbd className="text-[10px] font-mono text-[#A5A0C8] border border-[#2D264E] bg-[#0B0914] rounded-lg px-2 py-0.5">
            ESC
          </kbd>
        </div>

        {/* Command list */}
        <div className="p-3 max-h-80 overflow-y-auto space-y-1">
          {filtered.length === 0 ? (
            <div className="p-6 text-center text-xs text-[#A5A0C8]">No matching commands found.</div>
          ) : (
            filtered.map((item) => (
              <button
                key={item.id}
                onClick={item.action}
                className="w-full flex items-center justify-between p-3 rounded-2xl hover:bg-[#1E1938] transition-colors text-left group"
              >
                <div className="flex items-center gap-3">
                  <span className="text-base">{item.icon}</span>
                  <div>
                    <p className="text-xs font-bold text-white group-hover:text-[#C4B5FD]">{item.title}</p>
                    <p className="text-[10px] text-[#A5A0C8] font-mono">{item.category}</p>
                  </div>
                </div>
                <span className="text-[11px] text-[#8B5CF6] opacity-0 group-hover:opacity-100 font-mono transition-opacity">
                  Jump →
                </span>
              </button>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
