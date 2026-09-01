/**
 * GraphSearchBar — debounced search input for graph nodes.
 *
 * Rules:
 *   - Debounces at 300ms (DEBOUNCE_MS from config/constants).
 *   - Updates graphStore filters.search.
 *   - role="search" on wrapper.
 */

import { useRef, useEffect, useCallback } from 'react';
import { Input } from '@components/ui/Input';
import { UtilityIcons } from '@config/icons';
import { useGraphStore } from '@stores/graphStore';
import { DEBOUNCE_MS } from '@config/constants';

export function GraphSearchBar() {
  const setFilter   = useGraphStore((s) => s.setFilter);
  const searchValue = useGraphStore((s) => s.filters.search);
  const timerRef    = useRef<ReturnType<typeof setTimeout> | null>(null);

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
    <div role="search" aria-label="Search entities" className="relative w-64">
      <UtilityIcons.Search
        className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted pointer-events-none"
        aria-hidden="true"
      />
      <Input
        id="graph-search"
        type="search"
        placeholder="Search entities…"
        defaultValue={searchValue}
        onChange={handleChange}
        className="pl-9"
        aria-label="Search entities"
        autoComplete="off"
      />
    </div>
  );
}
