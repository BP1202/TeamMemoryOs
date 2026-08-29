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
import type { MemoryEntry, Scenario } from '@typedefs/memory';

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

// ─── Memory fixtures (full MemoryEntry shape) ──────────────────────────────

export const mockMemoryEntries: MemoryEntry[] = [
  {
    id: 'mem-01',
    organization_id: 'org-01',
    scenario_id: 'scn-01',
    created_by_user_id: 'usr-01',
    memory_type: 'decision',
    title: 'Adopt pgvector for semantic search',
    content: 'After evaluating Pinecone and pgvector, we decided to use pgvector because it integrates directly with our existing PostgreSQL instance.',
    meta: { source: 'ADR-001' },
    created_at: '2024-03-15T10:00:00Z',
    updated_at: '2024-03-15T10:00:00Z',
  },
  {
    id: 'mem-02',
    organization_id: 'org-01',
    scenario_id: null,
    created_by_user_id: 'usr-01',
    memory_type: 'insight',
    title: 'Database connection pool exhaustion',
    content: 'Production incident on 2024-03-10. Root cause: connection pool size set to 5, exhausted under load.',
    meta: null,
    created_at: '2024-03-10T08:30:00Z',
    updated_at: '2024-03-10T08:30:00Z',
  },
  {
    id: 'mem-03',
    organization_id: 'org-01',
    scenario_id: 'scn-01',
    created_by_user_id: null,
    memory_type: 'context',
    title: 'Team context: backend ownership',
    content: 'The backend team owns all services in the /backend directory. Frontend deploys independently.',
    meta: null,
    created_at: '2024-02-01T12:00:00Z',
    updated_at: '2024-02-01T12:00:00Z',
  },
];

export const mockMemoryEntry = mockMemoryEntries[0];

// ─── Scenario fixtures ─────────────────────────────────────────────────────

export const mockScenarios: Scenario[] = [
  {
    id: 'scn-01',
    organization_id: 'org-01',
    created_by_user_id: 'usr-01',
    name: 'Q4 Infrastructure',
    description: 'Infrastructure migration decisions for Q4.',
    is_active: true,
    created_at: '2024-01-15T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
  },
];

// ─── Legacy minimal fixtures (for dashboard service compat) ───────────────

export const mockMemoryList = mockMemoryEntries.map(({ id }) => ({ id }));
export const mockScenarioList = mockScenarios.map(({ id }) => ({ id }));

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

  // GET /api/v1/memory/organization/:orgId — returns full MemoryEntry list
  http.get(`${BASE}/api/v1/memory/organization/:orgId`, () => {
    return HttpResponse.json(mockMemoryEntries, { status: 200 });
  }),

  // GET /api/v1/memory/:id — single entry
  http.get(`${BASE}/api/v1/memory/:id`, ({ params }) => {
    const entry = mockMemoryEntries.find((m) => m.id === params.id);
    if (!entry) {
      return HttpResponse.json({ detail: 'Memory entry not found' }, { status: 404 });
    }
    return HttpResponse.json(entry, { status: 200 });
  }),

  // POST /api/v1/memory/ — create entry
  http.post(`${BASE}/api/v1/memory/`, async ({ request }) => {
    const body = await request.json() as Partial<MemoryEntry>;
    const created: MemoryEntry = {
      id: 'mem-new',
      organization_id: body.organization_id ?? 'org-01',
      scenario_id: body.scenario_id ?? null,
      created_by_user_id: 'usr-01',
      memory_type: body.memory_type ?? 'decision',
      title: body.title ?? null,
      content: body.content ?? '',
      meta: body.meta ?? null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    return HttpResponse.json(created, { status: 201 });
  }),

  // POST /api/v1/memory/search — semantic search
  http.post(`${BASE}/api/v1/memory/search`, () => {
    return HttpResponse.json(
      mockMemoryEntries.map((entry, i) => ({ entry, rank: i + 1 })),
      { status: 200 },
    );
  }),

  // GET /api/v1/scenarios/organization/:orgId
  http.get(`${BASE}/api/v1/scenarios/organization/:orgId`, () => {
    return HttpResponse.json(mockScenarios, { status: 200 });
  }),

  // POST /api/v1/scenarios/ — create scenario
  http.post(`${BASE}/api/v1/scenarios/`, async ({ request }) => {
    const body = await request.json() as Partial<Scenario>;
    const created: Scenario = {
      id: 'scn-new',
      organization_id: body.organization_id ?? 'org-01',
      created_by_user_id: 'usr-01',
      name: body.name ?? 'New Scenario',
      description: body.description ?? null,
      is_active: body.is_active ?? true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    return HttpResponse.json(created, { status: 201 });
  }),

  // GET /api/v1/agents/
  http.get(`${BASE}/api/v1/agents/`, () => {
    return HttpResponse.json(mockAgentList, { status: 200 });
  }),
];
