/**
 * Knowledge Graph types.
 * Field names mirror backend Pydantic schema field names exactly.
 *
 * Backend refs:
 *   - schemas/entity.py        → EntityRead
 *   - schemas/relationship.py  → RelationshipRead, NeighborRead
 *   - models/entity.py         → EntityType enum (UPPERCASE), RelationshipType enum (UPPERCASE)
 */

// ─── Entity Type ───────────────────────────────────────────────────────────
// Must match backend EntityType enum (models/entity.py) exactly.

export type EntityType =
  | 'PERSON'
  | 'REPOSITORY'
  | 'FILE'
  | 'SERVICE'
  | 'TECHNOLOGY'
  | 'INCIDENT'
  | 'PULL_REQUEST'
  | 'BRANCH'
  | 'API_ENDPOINT';

export const ENTITY_TYPES: EntityType[] = [
  'PERSON',
  'REPOSITORY',
  'FILE',
  'SERVICE',
  'TECHNOLOGY',
  'INCIDENT',
  'PULL_REQUEST',
  'BRANCH',
  'API_ENDPOINT',
];

export const ENTITY_TYPE_LABELS: Record<EntityType, string> = {
  PERSON:       'Person',
  REPOSITORY:   'Repository',
  FILE:         'File',
  SERVICE:      'Service',
  TECHNOLOGY:   'Technology',
  INCIDENT:     'Incident',
  PULL_REQUEST: 'Pull Request',
  BRANCH:       'Branch',
  API_ENDPOINT: 'API Endpoint',
};

/** CSS color token per entity type — used by graph nodes and legend. */
export const ENTITY_TYPE_COLORS: Record<EntityType, string> = {
  PERSON:       '#6366f1', // indigo
  REPOSITORY:   '#0ea5e9', // sky
  FILE:         '#64748b', // slate
  SERVICE:      '#10b981', // emerald
  TECHNOLOGY:   '#8b5cf6', // violet
  INCIDENT:     '#ef4444', // red
  PULL_REQUEST: '#f59e0b', // amber
  BRANCH:       '#06b6d4', // cyan
  API_ENDPOINT: '#f97316', // orange
};

// ─── Relationship Type ─────────────────────────────────────────────────────
// Must match backend RelationshipType enum (models/entity.py) exactly.

export type RelationshipType =
  | 'REFERENCES'
  | 'IMPLEMENTS'
  | 'FIXES'
  | 'DEPENDS_ON'
  | 'REVIEWED_BY'
  | 'RELATED_TO'
  | 'CAUSED_BY';

export const RELATIONSHIP_TYPES: RelationshipType[] = [
  'REFERENCES',
  'IMPLEMENTS',
  'FIXES',
  'DEPENDS_ON',
  'REVIEWED_BY',
  'RELATED_TO',
  'CAUSED_BY',
];

export const RELATIONSHIP_TYPE_LABELS: Record<RelationshipType, string> = {
  REFERENCES:  'References',
  IMPLEMENTS:  'Implements',
  FIXES:       'Fixes',
  DEPENDS_ON:  'Depends On',
  REVIEWED_BY: 'Reviewed By',
  RELATED_TO:  'Related To',
  CAUSED_BY:   'Caused By',
};

// ─── Entity ────────────────────────────────────────────────────────────────

export interface Entity {
  id: string;
  organization_id: string;
  entity_type: EntityType;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

// ─── Relationship ──────────────────────────────────────────────────────────

export interface Relationship {
  id: string;
  organization_id: string;
  source_entity_id: string;
  target_entity_id: string;
  relationship_type: RelationshipType;
  created_at: string;
}

// ─── Neighbor ─────────────────────────────────────────────────────────────

export interface Neighbor {
  entity: Entity;
  relationship_type: RelationshipType;
  relationship_id: string;
  direction: 'outgoing' | 'incoming';
}

// ─── UI filter state (client only) ────────────────────────────────────────

export interface GraphFilters {
  entityType: EntityType | 'all';
  relationshipType: RelationshipType | 'all';
  search: string;
}
