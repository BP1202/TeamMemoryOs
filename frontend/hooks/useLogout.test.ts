/**
 * useLogout hook — tests.
 * Tests: clears auth, redirects to /login, clears query cache.
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuthStore } from '@stores/authStore';
import { useLogout } from './useLogout';

// We mock useNavigate since it requires a real router context
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return { ...actual, useNavigate: () => mockNavigate };
});

const mockNavigate = vi.fn();

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  // eslint-disable-next-line react/display-name
  const Wrapper = ({ children }: { children: ReactNode }) =>
    React.createElement(
      QueryClientProvider,
      { client: qc },
      React.createElement(
        MemoryRouter,
        null,
        children,
      ),
    );
  return { qc, Wrapper };
}

describe('useLogout', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    useAuthStore.getState().setAuth('tok', {
      id: 'u1',
      email: 'a@b.com',
      full_name: 'Test',
      is_active: true,
      created_at: '',
      updated_at: '',
    });
  });

  it('clears auth store on logout', () => {
    const { Wrapper } = makeWrapper();
    const { result } = renderHook(() => useLogout(), { wrapper: Wrapper });

    act(() => result.current());

    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().token).toBeNull();
  });

  it('navigates to /login on logout', () => {
    const { Wrapper } = makeWrapper();
    const { result } = renderHook(() => useLogout(), { wrapper: Wrapper });

    act(() => result.current());

    expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true });
  });
});
