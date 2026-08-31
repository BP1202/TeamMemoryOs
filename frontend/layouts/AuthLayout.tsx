/**
 * AuthLayout — unauthenticated page wrapper.
 */

import { Outlet } from 'react-router-dom';

export function AuthLayout() {
  return (
    <div className="min-h-screen bg-[#0B0914] text-white w-full">
      <Outlet />
    </div>
  );
}
