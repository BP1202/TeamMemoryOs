/**
 * Tooltip provider from Radix UI.
 * Global tooltip delay configuration.
 */

import { Provider as RadixTooltipProvider } from '@radix-ui/react-tooltip';
import type { ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

export function TooltipProvider({ children }: Props) {
  return (
    <RadixTooltipProvider delayDuration={400} skipDelayDuration={0}>
      {children}
    </RadixTooltipProvider>
  );
}
