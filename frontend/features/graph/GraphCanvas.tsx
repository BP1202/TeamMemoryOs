/**
 * GraphCanvas — React Flow canvas with custom nodes, edges, controls.
 *
 * Features:
 *   - Custom EntityNode for each entity
 *   - Custom RelationshipEdge for each relationship
 *   - MiniMap, Controls, Background grid
 *   - GraphLegend overlay
 *   - Node click → selectEntity in store
 *   - Keyboard: Enter on selected node → expand
 *   - nodesDraggable: true (user can rearrange)
 *   - Progressive loading: initial load only; neighbors loaded on demand
 *
 * Performance:
 *   - useMemo for nodes and edges arrays
 *   - React Flow's built-in viewport virtualization
 *   - No unnecessary state in component — store manages selection
 *
 * Rules:
 *   - No direct API calls — data received as props.
 *   - Store reads only for selection/filter state.
 */

import { useMemo, useCallback } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  MiniMap,
  MarkerType,
  type Edge,
  type NodeMouseHandler,
  type OnInit,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { EntityNode }        from './EntityNode';
import { RelationshipEdge }  from './RelationshipEdge';
import { GraphLegend }       from './GraphLegend';
import { useGraphStore }     from '@stores/graphStore';
import { ENTITY_TYPE_COLORS } from '@typedefs/graph';
import type { Entity, Relationship } from '@typedefs/graph';
import type { EntityNodeData } from './EntityNode';

// ─── Node + edge type registry ─────────────────────────────────────────────

const nodeTypes = { entityNode: EntityNode };
const edgeTypes = { relationshipEdge: RelationshipEdge };

// ─── Layout helpers ────────────────────────────────────────────────────────

const GRID_COLS = 5;
const H_GAP     = 180;
const V_GAP     = 140;

function layoutEntities(entities: Entity[]): { id: string; x: number; y: number }[] {
  return entities.map((entity, i) => ({
    id: entity.id,
    x:  (i % GRID_COLS) * H_GAP,
    y:  Math.floor(i / GRID_COLS) * V_GAP,
  }));
}

// ─── Props ─────────────────────────────────────────────────────────────────

interface GraphCanvasProps {
  entities:      Entity[];
  relationships: Relationship[];
}

// ─── Inner canvas (must be inside ReactFlowProvider) ──────────────────────

function GraphCanvasInner({ entities, relationships }: GraphCanvasProps) {
  const selectedId  = useGraphStore((s) => s.selectedEntityId);
  const expandedIds = useGraphStore((s) => s.expandedEntityIds);
  const filters     = useGraphStore((s) => s.filters);
  const selectEntity  = useGraphStore((s) => s.selectEntity);

  // ── Client-side filter ─────────────────────────────────────────────────

  const filteredEntities = useMemo(() => {
    return entities.filter((e) => {
      if (filters.entityType !== 'all' && e.entity_type !== filters.entityType) return false;
      if (filters.search.trim()) {
        const q = filters.search.toLowerCase();
        if (!e.name.toLowerCase().includes(q) && !(e.description?.toLowerCase().includes(q) ?? false)) {
          return false;
        }
      }
      return true;
    });
  }, [entities, filters]);

  const filteredEntityIds = useMemo(
    () => new Set(filteredEntities.map((e) => e.id)),
    [filteredEntities],
  );

  const filteredRelationships = useMemo(() => {
    return relationships.filter((r) => {
      if (!filteredEntityIds.has(r.source_entity_id)) return false;
      if (!filteredEntityIds.has(r.target_entity_id)) return false;
      if (filters.relationshipType !== 'all' && r.relationship_type !== filters.relationshipType) return false;
      return true;
    });
  }, [relationships, filteredEntityIds, filters.relationshipType]);

  // ── Build React Flow nodes ─────────────────────────────────────────────

  const layout = useMemo(() => layoutEntities(filteredEntities), [filteredEntities]);

  const nodes = useMemo(() => {
    const searchQ = filters.search.toLowerCase().trim();
    return filteredEntities.map((entity, i) => {
      const pos = layout[i] ?? { x: 0, y: 0 };
      const isHighlighted = Boolean(
        searchQ && (
          entity.name.toLowerCase().includes(searchQ) ||
          entity.description?.toLowerCase().includes(searchQ)
        ),
      );
      return {
        id:       entity.id,
        type:     'entityNode',
        position: { x: pos.x, y: pos.y },
        data:     {
          entity,
          isSelected:    entity.id === selectedId,
          isExpanded:    expandedIds.includes(entity.id),
          isHighlighted,
        } as Record<string, unknown>,
        selected: entity.id === selectedId,
      };
    });
  }, [filteredEntities, layout, selectedId, expandedIds, filters.search]);

  // ── Build React Flow edges ─────────────────────────────────────────────

  const edges: Edge[] = useMemo(() => {
    return filteredRelationships.map((rel) => ({
      id:         rel.id,
      source:     rel.source_entity_id,
      target:     rel.target_entity_id,
      type:       'relationshipEdge',
      data:       { relationship_type: rel.relationship_type },
      markerEnd:  {
        type:       MarkerType.ArrowClosed,
        color:      '#475569',
        width:      12,
        height:     12,
      },
    }));
  }, [filteredRelationships]);

  // ── Interaction handlers ───────────────────────────────────────────────

  const handleNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => selectEntity(node.id),
    [selectEntity],
  );

  const handlePaneClick = useCallback(() => {
    // Do not deselect on canvas click — keep inspector open until explicitly closed
  }, []);

  const handleInit: OnInit = useCallback((_instance) => {
    // Could fit view here if desired
  }, []);

  // ── Minimap node color ────────────────────────────────────────────────

  const minimapNodeColor = useCallback((node: { data: Record<string, unknown> }) => {
    const d = node.data as unknown as EntityNodeData;
    return ENTITY_TYPE_COLORS[d.entity?.entity_type] ?? '#64748b';
  }, []);

  return (
    <div
      role="application"
      aria-label="Knowledge graph canvas"
      className="w-full h-full"
      data-testid="graph-canvas"
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        onInit={handleInit}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        minZoom={0.2}
        maxZoom={2.5}
        attributionPosition="bottom-right"
        aria-label="Knowledge graph"
      >
        <Background color="var(--color-border, #334155)" gap={24} size={1} />
        <Controls aria-label="Graph controls" />
        <MiniMap
          nodeColor={minimapNodeColor}
          maskColor="rgba(0,0,0,0.3)"
          aria-label="Graph minimap"
        />
        <GraphLegend />
      </ReactFlow>
    </div>
  );
}

// ─── Exported component (wraps with provider) ──────────────────────────────

export function GraphCanvas(props: GraphCanvasProps) {
  return (
    <ReactFlowProvider>
      <GraphCanvasInner {...props} />
    </ReactFlowProvider>
  );
}
