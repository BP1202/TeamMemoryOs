/**
 * DebugAgentPanel — error message + stack trace input with incident analysis output.
 *
 * Security:
 *   - Stack trace content is plain text textarea — never rendered as HTML.
 *   - Suggested actions rendered as <button> only.
 *
 * Accessibility:
 *   - Stack trace textarea: aria-label="Stack trace", spellCheck={false}.
 */

import { useForm } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import { StatusIcons } from '@config/icons';
import { Button } from '@components/ui/Button';
import { Input } from '@components/ui/Input';
import { ErrorState } from '@components/feedback/ErrorState';
import { useAuthStore } from '@stores/authStore';
import { analyzeDebug } from '@services/agentsService';
import { AIResponseCard } from '@features/chat/AIResponseCard';
import { ParsedTraceView } from './ParsedTraceView';
import type { DebugAnalyzeResponse } from '@typedefs/agents';
import { cn } from '@utils/cn';

interface DebugFormValues {
  error_message: string;
  stack_trace: string;
}

interface IncidentMatchItemProps {
  memoryTitle: string | null;
  similarity: number;
  resolution: string | null;
}

function IncidentMatchItem({ memoryTitle, similarity, resolution }: IncidentMatchItemProps) {
  const pct = Math.round(similarity * 100);
  return (
    <li className="p-3 bg-surface-subtle rounded border border-border space-y-1">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-text-primary">
          {memoryTitle ?? 'Untitled incident'}
        </span>
        <span
          className={cn(
            'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border',
            pct >= 75
              ? 'text-success bg-success/10 border-success/30'
              : pct >= 50
              ? 'text-warning bg-warning/10 border-warning/30'
              : 'text-text-muted bg-surface-elevated border-border',
          )}
          aria-label={`Match similarity: ${pct}%`}
        >
          <StatusIcons.success className="h-3 w-3" aria-hidden="true" />
          {pct}%
        </span>
      </div>
      {resolution && (
        <p className="text-xs text-text-secondary line-clamp-2">{resolution}</p>
      )}
    </li>
  );
}

export function DebugAgentPanel() {
  const orgId  = useAuthStore((s) => s.user?.id ?? '');
  const result = useMutation<DebugAnalyzeResponse, Error, DebugFormValues>({
    mutationFn: (values) =>
      analyzeDebug({
        organization_id: orgId,
        error_message: values.error_message,
        stack_trace: values.stack_trace || undefined,
      }),
  });

  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors },
  } = useForm<DebugFormValues>({ defaultValues: { error_message: '', stack_trace: '' } });

  const handleSuggestedAction = (action: string) => {
    result.mutate({ ...getValues(), error_message: action });
  };

  return (
    <div className="space-y-6" data-testid="debug-agent-panel">
      <form onSubmit={handleSubmit((v) => result.mutate(v))} className="space-y-4">

        {/* Error message */}
        <div className="space-y-1">
          <label htmlFor="debug-error-message" className="text-sm font-medium text-text-primary">
            Error Message
          </label>
          <Input
            id="debug-error-message"
            placeholder="e.g. ConnectionError: pool exhausted at connection 23"
            aria-describedby={errors.error_message ? 'debug-error-desc' : undefined}
            {...register('error_message', { required: 'An error message is required.' })}
          />
          {errors.error_message && (
            <p id="debug-error-desc" className="text-xs text-danger" role="alert">
              {errors.error_message.message}
            </p>
          )}
        </div>

        {/* Stack trace */}
        <div className="space-y-1">
          <label htmlFor="debug-stack-trace" className="text-sm font-medium text-text-primary">
            Stack Trace (optional)
          </label>
          <textarea
            id="debug-stack-trace"
            rows={8}
            aria-label="Stack trace"
            spellCheck={false}
            placeholder="Paste the full stack trace here…"
            className={cn(
              'w-full px-3 py-2 text-xs font-mono rounded-md border border-border',
              'bg-surface text-text-primary resize-y',
              'placeholder:text-text-muted',
              'focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent',
            )}
            {...register('stack_trace')}
          />
        </div>

        <Button
          type="submit"
          variant="primary"
          size="sm"
          isLoading={result.isPending}
        >
          <StatusIcons.warning className="h-3.5 w-3.5" aria-hidden="true" />
          Analyze
        </Button>
      </form>

      {result.isError && (
        <ErrorState
          heading="Debug analysis failed"
          message={result.error instanceof Error ? result.error.message : undefined}
          onRetry={() => result.reset()}
          retryLabel="Dismiss"
        />
      )}

      {result.data && (
        <div className="space-y-4" data-testid="debug-result">
          {/* AI analysis with full explainability */}
          <AIResponseCard
            content={result.data.analysis}
            explanation={result.data.explanation}
            provider_used={result.data.provider_used}
            created_at={new Date().toISOString()}
            suggested_actions={result.data.suggested_actions}
            onSuggestedAction={handleSuggestedAction}
          />

          {/* Related incident matches */}
          {result.data.incidents_found.length > 0 && (
            <section aria-labelledby="incidents-heading" className="space-y-2">
              <h4
                id="incidents-heading"
                className="text-xs font-semibold text-text-secondary uppercase tracking-wide"
              >
                Related Incidents ({result.data.incidents_found.length})
              </h4>
              <ul className="space-y-2" aria-label="Related incidents">
                {result.data.incidents_found.map((inc) => (
                  <IncidentMatchItem
                    key={inc.memory_id}
                    memoryTitle={inc.title}
                    similarity={inc.similarity}
                    resolution={inc.resolution}
                  />
                ))}
              </ul>
            </section>
          )}

          {/* Parsed stack trace if submitted */}
          {getValues('stack_trace') && (
            <section aria-labelledby="trace-heading" className="space-y-2">
              <h4
                id="trace-heading"
                className="text-xs font-semibold text-text-secondary uppercase tracking-wide"
              >
                Submitted Stack Trace
              </h4>
              <ParsedTraceView trace={getValues('stack_trace')} />
            </section>
          )}
        </div>
      )}
    </div>
  );
}
