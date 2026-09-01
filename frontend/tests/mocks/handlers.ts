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
import type { Entity, Relationship, Neighbor } from '@typedefs/graph';
import type { ChatAskResponse, RetrievalExplanationRead } from '@typedefs/chat';
import type {
  AgentListResponse,
  AgentRead,
  WorkflowPlanPreviewResponse,
  WorkflowRunResponse,
  RepositorySearchResponse,
  BranchListResponse,
  FileHistoryResponse,
  DebugAnalyzeResponse,
} from '@typedefs/agents';

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

export const mockAgentDetails: AgentRead[] = [
  {
    name: 'repository_agent',
    description: 'Searches and analyzes repository history, commits, and file changes.',
    capabilities: [
      { name: 'search_commits', description: 'Find commits by message or author.' },
      { name: 'file_history', description: 'List commit history for a specific file.' },
    ],
    is_active: true,
  },
  {
    name: 'debug_agent',
    description: 'Analyzes error messages and stack traces against past incidents.',
    capabilities: [
      { name: 'analyze_error', description: 'Match errors to historical incidents.' },
      { name: 'suggest_fix', description: 'Suggest remediation based on past resolutions.' },
    ],
    is_active: true,
  },
];

export const mockAgentList: AgentListResponse = {
  agents: mockAgentDetails,
  total: 2,
};

export const mockWorkflowPlan: WorkflowPlanPreviewResponse = {
  question: 'What changed in authentication last week?',
  selected_agents: ['repository_agent'],
  steps: [
    { step: 1, agent: 'planner',    description: 'Plan execution chain', estimated_duration_ms: 100 },
    { step: 2, agent: 'repository_agent', description: 'Search repository commits', estimated_duration_ms: 800 },
    { step: 3, agent: 'retriever',  description: 'Retrieve memory context', estimated_duration_ms: 400 },
    { step: 4, agent: 'granite',    description: 'Generate answer', estimated_duration_ms: 1200 },
    { step: 5, agent: 'explanation_builder', description: 'Build explanation', estimated_duration_ms: 200 },
    { step: 6, agent: 'debug_agent', description: 'Analyze for incidents', estimated_duration_ms: 600 },
  ],
  estimated_total_ms: 3300,
};

export const mockWorkflowRun: WorkflowRunResponse = {
  answer: 'Authentication was updated last week with a new JWT refresh token rotation mechanism.',
  provider_used: 'ibm-granite',
  participating_agents: ['repository_agent', 'granite'],
  steps: [
    { step: 1, agent: 'planner',    status: 'complete', duration_ms: 95,   memory_count: 0, citations_count: 0, description: 'Plan execution chain' },
    { step: 2, agent: 'repository_agent', status: 'complete', duration_ms: 820,  memory_count: 3, citations_count: 2, description: 'Searched repository' },
    { step: 3, agent: 'debug_agent', status: 'complete', duration_ms: 210,  memory_count: 1, citations_count: 0, description: 'Analyzed for incidents' },
    { step: 4, agent: 'retriever',  status: 'complete', duration_ms: 390,  memory_count: 5, citations_count: 3, description: 'Retrieve memory context' },
    { step: 5, agent: 'granite',    status: 'complete', duration_ms: 1150, memory_count: 0, citations_count: 0, description: 'Generate answer' },
    { step: 6, agent: 'explanation_builder', status: 'complete', duration_ms: 180, memory_count: 0, citations_count: 3, description: 'Build explanation' },
  ],
  total_duration_ms: 2845,
  explanation: {
    question: 'What changed in authentication last week?',
    retrieval_mode: 'hybrid',
    confidence: 0.85,
    result_count: 5,
    citations: [
      {
        memory_id: 'mem-01',
        memory_title: 'JWT refresh token rotation implemented',
        memory_type: 'decision',
        retrieval_reason: 'Direct match on authentication changes.',
        semantic_score: 0.92,
        graph_score: 0.1,
        link_score: 0.0,
        final_score: 0.87,
        graph_distance: 1,
        matched_entities: ['AuthService'],
        rank: 1,
      },
    ],
    graph_path: [
      {
        source_entity_id: 'ent-01',
        source_entity_name: 'AuthService',
        relationship_type: 'DEPENDS_ON',
        target_entity_id: 'ent-02',
        target_entity_name: 'PostgreSQL',
      },
    ],
    summary: 'Authentication changes retrieved from repository history and matched against memory.',
  },
  suggested_actions: [
    'Show all auth-related commits from last month',
    'What incidents involved authentication?',
  ],
};

export const mockRepositorySearch: RepositorySearchResponse = {
  answer: 'Recent auth module changes include JWT rotation and session expiry updates.',
  branch: 'main',
  commits: [
    { sha: 'a1b2c3d4e5f6', message: 'feat: add JWT refresh token rotation', author: 'alice', date: '2024-03-14T10:00:00Z', files_changed: 3 },
    { sha: 'b2c3d4e5f6a1', message: 'fix: session expiry edge case', author: 'bob', date: '2024-03-13T09:00:00Z', files_changed: 1 },
  ],
  provider_used: 'ibm-granite',
  explanation: null,
  suggested_actions: ['Show file history for auth.py'],
};

export const mockBranches: BranchListResponse = {
  branches: ['main', 'dev', 'feat/auth-refresh', 'feat/frontend-ai-workspace'],
};

export const mockFileHistory: FileHistoryResponse = {
  file_path: 'backend/app/api/routes/auth.py',
  branch: 'main',
  commits: [
    { sha: 'a1b2c3d4e5f6', message: 'feat: add JWT refresh token rotation', author: 'alice', date: '2024-03-14T10:00:00Z', files_changed: 3 },
  ],
};

export const mockDebugAnalysis: DebugAnalyzeResponse = {
  analysis: 'This error matches a known pool exhaustion incident from 2024-03-10. Root cause was pool_size=5.',
  incidents_found: [
    { memory_id: 'mem-02', title: 'Database connection pool exhaustion', similarity: 0.94, resolution: 'Increase pool_size to 20 in SQLAlchemy config.' },
  ],
  suggested_actions: ['Check pool_size configuration', 'Review recent connection usage'],
  provider_used: 'ibm-granite',
  explanation: null,
};

// ─── Entity + Relationship fixtures ────────────────────────────────────────

export const mockEntities: Entity[] = [
  {
    id:              'ent-01',
    organization_id: 'org-01',
    entity_type:     'SERVICE',
    name:            'AuthService',
    description:     'Handles authentication and JWT issuance.',
    created_at:      '2024-01-01T00:00:00Z',
    updated_at:      '2024-01-01T00:00:00Z',
  },
  {
    id:              'ent-02',
    organization_id: 'org-01',
    entity_type:     'TECHNOLOGY',
    name:            'PostgreSQL',
    description:     'Primary relational database.',
    created_at:      '2024-01-02T00:00:00Z',
    updated_at:      '2024-01-02T00:00:00Z',
  },
  {
    id:              'ent-03',
    organization_id: 'org-01',
    entity_type:     'PERSON',
    name:            'Alice Engineer',
    description:     null,
    created_at:      '2024-01-03T00:00:00Z',
    updated_at:      '2024-01-03T00:00:00Z',
  },
];

export const mockRelationships: Relationship[] = [
  {
    id:                'rel-01',
    organization_id:   'org-01',
    source_entity_id:  'ent-01',
    target_entity_id:  'ent-02',
    relationship_type: 'DEPENDS_ON',
    created_at:        '2024-01-01T00:00:00Z',
  },
];

export const mockNeighbors: Neighbor[] = [
  {
    entity:            mockEntities[1],
    relationship_type: 'DEPENDS_ON',
    relationship_id:   'rel-01',
    direction:         'outgoing',
  },
];

// ─── Chat fixtures ─────────────────────────────────────────────────────────

export const mockExplanation: RetrievalExplanationRead = {
  question:       'How do we handle authentication?',
  retrieval_mode: 'semantic',
  confidence:     0.87,
  result_count:   2,
  citations: [
    {
      memory_id:         'mem-01',
      memory_title:      'Adopt pgvector for semantic search',
      memory_type:       'decision',
      retrieval_reason:  'Directly relevant to the question asked.',
      semantic_score:    0.91,
      graph_score:       0.0,
      link_score:        0.0,
      final_score:       0.91,
      graph_distance:    0,
      matched_entities:  ['AuthService'],
      rank:              1,
    },
  ],
  graph_path: [
    {
      source_entity_id:   'ent-01',
      source_entity_name: 'AuthService',
      relationship_type:  'DEPENDS_ON',
      target_entity_id:   'ent-02',
      target_entity_name: 'PostgreSQL',
    },
  ],
  summary: 'Authentication is handled by the AuthService using JWT tokens and PostgreSQL for storage.',
};

export const mockChatResponse: ChatAskResponse = {
  answer:                 'Authentication is handled via JWT tokens issued by the AuthService.',
  citations:              ['mem-01'],
  retrieved_memory_count: 2,
  provider_used:          'ibm-granite',
  retrieval_mode:         'semantic',
  explanation:            mockExplanation,
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

  // GET /api/v1/agents/:name
  http.get(`${BASE}/api/v1/agents/:name`, ({ params }) => {
    const agent = mockAgentDetails.find((a) => a.name === params.name);
    if (!agent) return HttpResponse.json({ detail: 'Agent not found' }, { status: 404 });
    return HttpResponse.json(agent, { status: 200 });
  }),

  // POST /api/v1/agents/workflow/plan
  http.post(`${BASE}/api/v1/agents/workflow/plan`, () => {
    return HttpResponse.json(mockWorkflowPlan, { status: 200 });
  }),

  // POST /api/v1/agents/workflow/run
  http.post(`${BASE}/api/v1/agents/workflow/run`, () => {
    return HttpResponse.json(mockWorkflowRun, { status: 200 });
  }),

  // POST /api/v1/agents/repository/search
  http.post(`${BASE}/api/v1/agents/repository/search`, () => {
    return HttpResponse.json(mockRepositorySearch, { status: 200 });
  }),

  // GET /api/v1/agents/repository/branches
  http.get(`${BASE}/api/v1/agents/repository/branches`, () => {
    return HttpResponse.json(mockBranches, { status: 200 });
  }),

  // POST /api/v1/agents/repository/file-history
  http.post(`${BASE}/api/v1/agents/repository/file-history`, () => {
    return HttpResponse.json(mockFileHistory, { status: 200 });
  }),

  // POST /api/v1/agents/debug/analyze
  http.post(`${BASE}/api/v1/agents/debug/analyze`, () => {
    return HttpResponse.json(mockDebugAnalysis, { status: 200 });
  }),

  // ── Entity handlers ────────────────────────────────────────────────────

  // GET /api/v1/entities/organization/:orgId
  http.get(`${BASE}/api/v1/entities/organization/:orgId`, () => {
    return HttpResponse.json(mockEntities, { status: 200 });
  }),

  // GET /api/v1/entities/memory/:memoryId
  http.get(`${BASE}/api/v1/entities/memory/:memoryId`, () => {
    return HttpResponse.json([mockEntities[0]], { status: 200 });
  }),

  // GET /api/v1/entities/:id
  http.get(`${BASE}/api/v1/entities/:id`, ({ params }) => {
    const entity = mockEntities.find((e) => e.id === params.id);
    if (!entity) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    return HttpResponse.json(entity, { status: 200 });
  }),

  // ── Relationship handlers ──────────────────────────────────────────────

  // GET /api/v1/relationships/entity/:id/outgoing
  http.get(`${BASE}/api/v1/relationships/entity/:id/outgoing`, () => {
    return HttpResponse.json(mockRelationships, { status: 200 });
  }),

  // GET /api/v1/relationships/entity/:id/neighbors
  http.get(`${BASE}/api/v1/relationships/entity/:id/neighbors`, () => {
    return HttpResponse.json(mockNeighbors, { status: 200 });
  }),

  // GET /api/v1/relationships/:id
  http.get(`${BASE}/api/v1/relationships/:id`, ({ params }) => {
    const rel = mockRelationships.find((r) => r.id === params.id);
    if (!rel) return HttpResponse.json({ detail: 'Not found' }, { status: 404 });
    return HttpResponse.json(rel, { status: 200 });
  }),

  // ── Chat handler ──────────────────────────────────────────────────────

  // POST /api/v1/chat/ask
  http.post(`${BASE}/api/v1/chat/ask`, () => {
    return HttpResponse.json(mockChatResponse, { status: 200 });
  }),
];
