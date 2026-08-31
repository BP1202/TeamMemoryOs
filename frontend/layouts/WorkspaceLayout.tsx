/**
 * WorkspaceLayout — authenticated workspace wrapper.
 * Renders AppShell. Protected by AuthGuard in the router.
 */

import { AppShell } from './AppShell';

export function WorkspaceLayout() {
  return <AppShell />;
}
