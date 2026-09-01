/**
 * Motion provider.
 * Wraps Framer Motion's LazyMotion for performance.
 * All reduced-motion checks happen at animation sites via useReducedMotion().
 */

import type { ReactNode } from 'react';
import { LazyMotion, domAnimation } from 'framer-motion';

interface Props {
  children: ReactNode;
}

export function MotionProvider({ children }: Props) {
  return <LazyMotion features={domAnimation}>{children}</LazyMotion>;
}
