/**
 * Chat workspace types.
 * Mirrors backend ChatAskRequest / ChatAskResponse + RetrievalExplanationRead schemas.
 *
 * Rules:
 *   - Field names match backend Pydantic schema exactly.
 *   - No runtime logic or default values.
 */

// ─── Request ────────────────────────────────────────────────────────────────

export interface ChatAskRequest {
  organization_id: string;
  question: string;
  top_k?: number;
  scenario_id?: string | null;
  use_hybrid?: boolean;
}

// ─── Explanation sub-types ──────────────────────────────────────────────────

export interface CitationRead {
  memory_id: string;
  memory_title: string | null;
  memory_type: string;
  retrieval_reason: string;
  semantic_score: number;
  graph_score: number;
  link_score: number;
  final_score: number;
  graph_distance: number;
  matched_entities: string[];
  rank: number;
}

export interface GraphPathStepRead {
  source_entity_id: string;
  source_entity_name: string;
  relationship_type: string;
  target_entity_id: string;
  target_entity_name: string;
}

export interface RetrievalExplanationRead {
  question: string;
  retrieval_mode: string;
  confidence: number;
  result_count: number;
  citations: CitationRead[];
  graph_path: GraphPathStepRead[];
  summary: string;
}

// ─── Response ───────────────────────────────────────────────────────────────

export interface ChatAskResponse {
  answer: string;
  citations: string[];
  retrieved_memory_count: number;
  provider_used: string;
  retrieval_mode: string;
  explanation: RetrievalExplanationRead | null;
}

// ─── Client-side chat message (assembled in chatStore, not from API) ────────

export type ChatMessageRole = 'user' | 'assistant';

export interface ChatMessage {
  /** Client-generated UUID for the message. */
  id: string;
  role: ChatMessageRole;
  content: string;
  /** Timestamp (ISO string) when the message was created. */
  created_at: string;
  /** Populated only for assistant messages that have an explanation. */
  explanation: RetrievalExplanationRead | null;
  /** Populated only for assistant messages with suggested follow-up questions. */
  suggested_actions?: string[];
  /** Whether this assistant message is currently streaming/loading. */
  isLoading?: boolean;
  /** Error message if this assistant turn failed. */
  error?: string;
}

export interface ChatSession {
  /** Current scenario filter (null = all scenarios). */
  scenario_id: string | null;
  /** Whether to use hybrid retrieval mode. */
  use_hybrid: boolean;
}
