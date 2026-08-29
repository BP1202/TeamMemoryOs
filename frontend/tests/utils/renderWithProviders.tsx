/**
 * Test utilities — custom render with all providers.
 *
 * Use `renderWithProviders` instead of `render` in all component tests.
 */

import { render, type RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import type { ReactElement, ReactNode } from 'react';

// ─── QueryClient factory for tests (no retries, no cache) ─────────────────

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
}

// ─── Wrapper ───────────────────────────────────────────────────────────────

interface WrapperOptions {
  initialPath?: string;
}

function createWrapper({ initialPath = '/' }: WrapperOptions = {}) {
  const queryClient = createTestQueryClient();

  function TestWrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter
          initialEntries={[initialPath]}
          future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
        >
          <Routes>
            <Route path="*" element={children} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );
  }

  return TestWrapper;
}

// ─── Custom render ─────────────────────────────────────────────────────────

export function renderWithProviders(
  ui: ReactElement,
  options: Omit<RenderOptions, 'wrapper'> & WrapperOptions = {},
) {
  const { initialPath, ...renderOptions } = options;
  const Wrapper = createWrapper({ initialPath });
  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

// Re-export everything from RTL for convenience
export * from '@testing-library/react';
export { renderWithProviders as render };
