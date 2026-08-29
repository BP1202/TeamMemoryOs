/**
 * MemorySearchBar — debounced search input for memory entries.
 *
 * Rules:
 *   - Debounces input at 300ms (DEBOUNCE_MS from config/constants).
 *   - role="search" on the wrapper.
 *   - Updates memoryStore filters.search.
 */

import { useRef, useEffect, useCallback } from 'react';
import { Input } from '@components/ui/Input';
import { UtilityIcons } from '@config/icons';
import { useMemoryStore } from '@stores/memoryStore';
import { DEBOUNCE_MS } from '@config/constants';

export function MemorySearchBar() {
  const setFilter   = useMemoryStore((s) => s.setFilter);
  const searchValue = useMemoryStore((s) => s.filters.search);
  const timerRef    = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Clear timer on unmount
  useEffect(() => () => {
    if (timerRef.current) clearTimeout(timerRef.current);
  }, []);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        setFilter({ search: value });
      }, DEBOUNCE_MS);
    },
    [setFilter],
  );

  return (
    <div role="search" aria-label="Search memories" className="relative w-full max-w-sm">
      <UtilityIcons.Search
        className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted pointer-events-none"
        aria-hidden="true"
      />
      <Input
        id="memory-search"
        type="search"
        placeholder="Search memories…"
        defaultValue={searchValue}
        onChange={handleChange}
        className="pl-9"
        aria-label="Search memories"
        autoComplete="off"
      />
    </div>
  );
}
