/**
 * Theme provider.
 * Applies the 'dark' class to <html> based on UI store preference.
 * Supports dark | light | system.
 */

import { useEffect, type ReactNode } from 'react';
import { useUIStore } from '@stores/uiStore';

interface Props {
  children: ReactNode;
}

export function ThemeProvider({ children }: Props) {
  const theme = useUIStore((s) => s.theme);

  useEffect(() => {
    const root = document.documentElement;

    const applyDark = () => {
      root.classList.add('dark');
      root.classList.remove('light');
    };
    const applyLight = () => {
      root.classList.add('light');
      root.classList.remove('dark');
    };

    if (theme === 'dark') {
      applyDark();
    } else if (theme === 'light') {
      applyLight();
    } else {
      // system
      const mq = window.matchMedia('(prefers-color-scheme: dark)');
      mq.matches ? applyDark() : applyLight();

      const handler = (e: MediaQueryListEvent) =>
        e.matches ? applyDark() : applyLight();
      mq.addEventListener('change', handler);
      return () => mq.removeEventListener('change', handler);
    }
  }, [theme]);

  return <>{children}</>;
}
