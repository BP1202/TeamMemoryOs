/**
 * Root provider — composes all global providers in correct order.
 *
 * Order:
 *   QueryProvider (React Query)
 *     ThemeProvider (reads UI store, applies dark class)
 *       MotionProvider (Framer Motion LazyMotion)
 *         TooltipProvider (Radix global tooltip)
 *
 * Note: ApiInterceptorBootstrap requires Router context (for navigate),
 * so it is registered inside AppRouter, not here.
 */

import type { ReactNode } from 'react';
import { QueryProvider } from './QueryProvider';
import { ThemeProvider } from './ThemeProvider';
import { MotionProvider } from './MotionProvider';
import { TooltipProvider } from './TooltipProvider';

interface Props {
  children: ReactNode;
}

export function RootProvider({ children }: Props) {
  return (
    <QueryProvider>
      <ThemeProvider>
        <MotionProvider>
          <TooltipProvider>{children}</TooltipProvider>
        </MotionProvider>
      </ThemeProvider>
    </QueryProvider>
  );
}
