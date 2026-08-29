/**
 * MSW handlers — mock API endpoints for tests.
 *
 * Rules:
 *   - No real network calls in tests.
 *   - Mirror backend route shapes exactly.
 *   - Add handlers here as new endpoints are integrated.
 */

import { http, HttpResponse } from 'msw';
import type { LoginResponse } from '@typedefs/auth';

const BASE = 'http://localhost:8000';

// ─── Mock data fixtures ────────────────────────────────────────────────────

export const mockUser = {
  id: 'usr-01',
  email: 'engineer@example.com',
  full_name: 'Test Engineer',
  role: 'member' as const,
  organization_id: 'org-01',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
};

export const mockLoginResponse: LoginResponse = {
  access_token: 'mock-jwt-token',
  token_type: 'bearer',
  user: mockUser,
};

// ─── Handlers ─────────────────────────────────────────────────────────────

export const handlers = [
  // POST /api/v1/auth/login
  http.post(`${BASE}/api/v1/auth/login`, async ({ request }) => {
    const body = await request.json() as { email?: string; password?: string };

    if (!body.email || !body.password) {
      return HttpResponse.json(
        { code: 'VALIDATION_ERROR', detail: 'Email and password are required' },
        { status: 422 },
      );
    }

    if (body.email === 'bad@example.com') {
      return HttpResponse.json(
        { code: 'INVALID_CREDENTIALS', detail: 'Invalid email or password' },
        { status: 401 },
      );
    }

    return HttpResponse.json(mockLoginResponse, { status: 200 });
  }),

  // GET /api/v1/auth/me
  http.get(`${BASE}/api/v1/auth/me`, () => {
    return HttpResponse.json(mockUser, { status: 200 });
  }),
];
