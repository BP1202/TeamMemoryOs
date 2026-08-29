/**
 * RootLayout — top-level layout.
 * Renders Outlet only — no UI chrome.
 * Provider composition happens in RootProvider.
 */

import { Outlet } from 'react-router-dom';

export function RootLayout() {
  return <Outlet />;
}
