/**
 * AuthLayout — unauthenticated page wrapper.
 * Centered, full-screen layout for login/register pages.
 */

import { Outlet } from 'react-router-dom';
import { APP_NAME } from '@config/constants';

export function AuthLayout() {
  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center bg-surface-base px-4"
      role="main"
    >
      {/* Logo */}
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-semibold text-text-primary">{APP_NAME}</h1>
        <p className="text-sm text-text-secondary mt-1">
          AI Operating System for Engineering Teams
        </p>
      </div>

      {/* Auth form container */}
      <div className="w-full max-w-sm">
        <Outlet />
      </div>
    </div>
  );
}
