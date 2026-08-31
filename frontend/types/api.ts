/**
 * API-level types shared across services.
 * Every type here mirrors the backend Pydantic schema field names exactly.
 */

// ─── Base response wrapper ─────────────────────────────────────────────────

export interface ApiError {
  status: number;
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ─── Common backend enums ──────────────────────────────────────────────────

// MemoryType is defined in types/memory.ts (mirrors backend enum).
// Re-exported here for backward compatibility.
import type { MemoryType } from './memory';
export type { MemoryType };

export type EntityType =
  | 'person'
  | 'technology'
  | 'repository'
  | 'service'
  | 'api'
  | 'pull_request'
  | 'branch';

export type RetrievalMode = 'semantic' | 'hybrid' | 'engineering';

// ─── AI Explainability ─────────────────────────────────────────────────────

export interface Citation {
  memory_id: string;
  title: string;
  memory_type: MemoryType;
  relevance_score: number;
  excerpt: string;
  created_at: string;
}

export interface ExplainabilityPayload {
  confidence_score: number;
  retrieval_mode: RetrievalMode;
  citations: Citation[];
  graph_path: string[];
  participating_agents: string[];
}

// ─── Health ───────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  service: string;
  version: string;
}

export interface DbHealthResponse {
  status: 'healthy' | 'unhealthy';
  database: string;
}

// ─── Dashboard counts ─────────────────────────────────────────────────────

export interface DashboardStats {
  memoryCount: number;
  scenarioCount: number;
  agentCount: number;
}
