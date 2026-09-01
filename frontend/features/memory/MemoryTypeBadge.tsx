/**
 * MemoryTypeBadge — memory type visual indicator.
 * Renders a Badge with an icon and label for each MemoryType.
 * Pure display component — no store or service reads.
 */

import { Badge } from '@components/ui/Badge';
import { MemoryTypeIcons } from '@config/icons';
import { MEMORY_TYPE_LABELS } from '@typedefs/memory';
import type { MemoryType } from '@typedefs/memory';
import type { BadgeVariant } from '@typedefs/ui';

// ─── Variant map ───────────────────────────────────────────────────────────

const BADGE_VARIANT: Record<MemoryType, BadgeVariant> = {
  decision:   'info',
  context:    'default',
  artifact:   'success',
  insight:    'warning',
  discussion: 'default',
};

// ─── Props ─────────────────────────────────────────────────────────────────

interface MemoryTypeBadgeProps {
  type: MemoryType;
  className?: string;
}

// ─── Component ─────────────────────────────────────────────────────────────

const ICON_KEY_MAP: Record<MemoryType, keyof typeof MemoryTypeIcons> = {
  decision:   'DECISION',
  context:    'DOCUMENTATION',  // closest semantic match
  artifact:   'CODE',
  insight:    'DECISION',
  discussion: 'DISCUSSION',
};

export function MemoryTypeBadge({ type, className }: MemoryTypeBadgeProps) {
  const Icon = MemoryTypeIcons[ICON_KEY_MAP[type]];

  const label = MEMORY_TYPE_LABELS[type] ?? type;
  const variant = BADGE_VARIANT[type] ?? 'default';

  return (
    <Badge variant={variant} className={className}>
      {Icon && <Icon className="h-3 w-3" aria-hidden="true" />}
      {label}
    </Badge>
  );
}
