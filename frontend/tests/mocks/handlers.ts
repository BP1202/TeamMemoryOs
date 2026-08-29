/**
 * MSW handlers — mock API endpoints for tests.
 *
 * Rules:
 *   - No real network calls in tests.
 *   - Mirror backend route shapes exactly.
 *   - Auth login uses OAuth2 form-data (username/password).
 *   - Token response has no `user` field — profile fetched from /users/me.
 */

import { http, HttpResponse } from 'msw';
import type { User, LoginResponse } from '@typedefs/auth';
import type { HealthResponse, DbHealthResponse } from '@typedefs/api';

const BASE = 'http://localhost:8000';

// ─── Mock data fixtures ────────────────────────────────────────────────────

export const mockUser: User = {
  id: 'usr-01',
  email: 'engineer@example.com',
  full_name: 'Test Engineer',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockLoginResponse: LoginResponse = {
  access_token: 'mock-jwt-token',
  token_type: 'bearer',
};

export const mockHealth: HealthResponse = {
  status: 'healthy',
  service: 'TeamMemory OS Backend',
  version: '0.1.0',
};

export const mockDbHealth: DbHealthResponse = {
  status: 'healthy',
  database: 'connected',
};

export const mockMemoryList = [
  { id: 'mem-01' },
  { id: 'mem-02' },
  { id: 'mem-03' },
];

export const mockScenarioList = [{ id: 'scn-01' }];

export const mockAgentList = {
  agents: [{ name: 'repository_agent' }, { name: 'debug_agent' }],
  total: 2,
};

// ─── Handlers ─────────────────────────────────────────────────────────────

export const handlers = [
  // POST /api/v1/auth/login — OAuth2 form-data
  http.post(`${BASE}/api/v1/auth/login`, async ({ request }) => {
    const text = await request.text();
    const params = new URLSearchParams(text);
    const username = params.get('username');
    const password = params.get('password');

    if (!username || !password) {
      return HttpResponse.json(
        { detail: 'Email and password are required' },
        { status: 422 },
      );
    }

    if (username === 'bad@example.com') {
      return HttpResponse.json(
        { detail: 'Incorrect email or password' },
        { status: 401 },
      );
    }

    return HttpResponse.json(mockLoginResponse, { status: 200 });
  }),

  // GET /api/v1/users/me
  http.get(`${BASE}/api/v1/users/me`, () => {
    return HttpResponse.json(mockUser, { status: 200 });
  }),

  // GET /api/v1/health/
  http.get(`${BASE}/api/v1/health/`, () => {
    return HttpResponse.json(mockHealth, { status: 200 });
  }),

  // GET /api/v1/health/db
  http.get(`${BASE}/api/v1/health/db`, () => {
    return HttpResponse.json(mockDbHealth, { status: 200 });
  }),

  // GET /api/v1/memory/organization/:id
  http.get(`${BASE}/api/v1/memory/organization/:orgId`, () => {
    return HttpResponse.json(mockMemoryList, { status: 200 });
  }),

  // GET /api/v1/scenarios/organization/:id
  http.get(`${BASE}/api/v1/scenarios/organization/:orgId`, () => {
    return HttpResponse.json(mockScenarioList, { status: 200 });
  }),

  // GET /api/v1/agents/
  http.get(`${BASE}/api/v1/agents/`, () => {
    return HttpResponse.json(mockAgentList, { status: 200 });
  }),
];
