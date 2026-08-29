/**
 * AuthGuard — routing tests.
 */

import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '@stores/authStore';
import { AuthGuard } from './AuthGuard';

function setup(isAuthenticated: boolean) {
  const store = useAuthStore.getState();
  if (isAuthenticated) {
    store.setAuth('mock-token', {
      id: 'u1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'member',
      organization_id: 'org-1',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
    });
  } else {
    store.clearAuth();
  }

  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter
        initialEntries={['/dashboard']}
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        <Routes>
          <Route
            path="/dashboard"
            element={
              <AuthGuard>
                <div>Protected content</div>
              </AuthGuard>
            }
          />
          <Route path="/login" element={<div>Login page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('AuthGuard', () => {
  it('renders protected content when authenticated', () => {
    setup(true);
    expect(screen.getByText('Protected content')).toBeInTheDocument();
  });

  it('redirects to /login when not authenticated', () => {
    setup(false);
    expect(screen.getByText('Login page')).toBeInTheDocument();
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument();
  });
});
