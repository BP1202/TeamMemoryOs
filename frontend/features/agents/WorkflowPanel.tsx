/**
 * WorkflowPanel — workflow question form with agent multi-select,
 * dry-run preview, and execution results.
 *
 * Architecture:
 *   - React Hook Form for form state.
 *   - useMutation for dry-run (plan) and execute (run).
 *   - agentStore.addWorkflowTurn() called on successful run.
 *   - All AI responses render all 5 explainability fields via AIResponseCard.
 */

import { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery } from '@tanstack/react-query';
import { NavIcons, UtilityIcons } from '@config/icons';
import { Button } from '@components/ui/Button';
import { Input } from '@components/ui/Input';
import { ErrorState } from '@components/feedback/ErrorState';
import { useAuthStore } from '@stores/authStore';
import { useAgentStore } from '@stores/agentStore';
import { planWorkflow, runWorkflow } from '@services/agentsService';
import { listAgents } from '@services/agentsService';
import { AIResponseCard } from '@features/chat/AIResponseCard';
import { WorkflowPlanPreview } from './WorkflowPlanPreview';
import { WorkflowTimeline } from './WorkflowTimeline';
import { ExecutionMetricsBadge } from './ExecutionMetricsBadge';
import { AGENTS_QUERY_KEY } from './AgentRegistryGrid';
import { cn } from '@utils/cn';
import type { WorkflowRunResponse, WorkflowPlanPreviewResponse } from '@typedefs/agents';

interface WorkflowFormValues {
  question: string;
}

export function WorkflowPanel() {
  const orgId = useAuthStore((s) => s.user?.id ?? '');
  const addWorkflowTurn = useAgentStore((s) => s.addWorkflowTurn);

  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [planResult,     setPlanResult]     = useState<WorkflowPlanPreviewResponse | null>(null);
  const [runResult,      setRunResult]      = useState<WorkflowRunResponse | null>(null);

  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors },
  } = useForm<WorkflowFormValues>({ defaultValues: { question: '' } });

  // ─── Agent list for multi-select ──────────────────────────────────────────
  const agentsQ = useQuery({
    queryKey: AGENTS_QUERY_KEY,
    queryFn: ({ signal }) => listAgents(signal),
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(orgId),
  });

  const availableAgents = agentsQ.data?.agents ?? [];

  const toggleAgent = (name: string) => {
    setSelectedAgents((prev) =>
      prev.includes(name) ? prev.filter((a) => a !== name) : [...prev, name],
    );
  };

  // ─── Dry-run plan mutation ─────────────────────────────────────────────────
  const planMutation = useMutation({
    mutationFn: (q: string) =>
      planWorkflow({
        organization_id: orgId,
        question: q,
        agents: selectedAgents.length > 0 ? selectedAgents : undefined,
      }),
    onSuccess: (data) => {
      setPlanResult(data);
      setRunResult(null);
    },
  });

  // ─── Execute workflow mutation ─────────────────────────────────────────────
  const runMutation = useMutation({
    mutationFn: (q: string) =>
      runWorkflow({
        organization_id: orgId,
        question: q,
        agents: selectedAgents.length > 0 ? selectedAgents : undefined,
      }),
    onSuccess: (data) => {
      setRunResult(data);
      setPlanResult(null);
      addWorkflowTurn({
        id: `wf-${Date.now()}`,
        question: getValues('question'),
        response: data,
        created_at: new Date().toISOString(),
      });
    },
  });

  // ─── Handlers ─────────────────────────────────────────────────────────────

  const onDryRun = useCallback(
    handleSubmit(({ question }) => {
      planMutation.mutate(question);
    }),
    [handleSubmit, planMutation],
  );

  const onExecute = useCallback(
    handleSubmit(({ question }) => {
      runMutation.mutate(question);
    }),
    [handleSubmit, runMutation],
  );

  const handleSuggestedAction = (action: string) => {
    runMutation.mutate(action);
  };

  // ─── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6" data-testid="workflow-panel">
      {/* Question form */}
      <form onSubmit={onExecute} className="space-y-4">
        <div className="space-y-1">
          <label htmlFor="workflow-question" className="text-sm font-medium text-text-primary">
            Question
          </label>
          <div className="flex gap-2">
            <Input
              id="workflow-question"
              placeholder="Ask the multi-agent system a question…"
              className="flex-1"
              aria-describedby={errors.question ? 'workflow-question-error' : undefined}
              {...register('question', {
                required: 'A question is required.',
                minLength: { value: 5, message: 'At least 5 characters required.' },
              })}
            />
          </div>
          {errors.question && (
            <p id="workflow-question-error" className="text-xs text-danger mt-1" role="alert">
              {errors.question.message}
            </p>
          )}
        </div>

        {/* Agent multi-select */}
        {availableAgents.length > 0 && (
          <div className="space-y-1">
            <span className="text-sm font-medium text-text-primary">
              Select agents (optional — defaults to all)
            </span>
            <div className="flex flex-wrap gap-2" role="group" aria-label="Agent selection">
              {availableAgents.map((agent) => {
                const checked = selectedAgents.includes(agent.name);
                return (
                  <button
                    key={agent.name}
                    type="button"
                    onClick={() => toggleAgent(agent.name)}
                    aria-pressed={checked}
                    className={cn(
                      'px-3 py-1.5 text-xs rounded-md border transition-colors',
                      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
                      checked
                        ? 'bg-purple-50 border-purple-300 text-purple-700 dark:bg-purple-900/30 dark:border-purple-700 dark:text-purple-300'
                        : 'bg-surface-subtle border-border text-text-secondary hover:bg-surface-elevated',
                    )}
                  >
                    {agent.name.replace(/_/g, ' ')}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-2 flex-wrap">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={onDryRun}
            isLoading={planMutation.isPending}
            aria-label="Preview workflow plan (dry run — not executed)"
          >
            <NavIcons.Agents className="h-3.5 w-3.5" aria-hidden="true" />
            Dry Run Preview
          </Button>

          <Button
            type="submit"
            variant="primary"
            size="sm"
            isLoading={runMutation.isPending}
            aria-label="Execute workflow"
          >
            <UtilityIcons.ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
            Execute Workflow
          </Button>
        </div>
      </form>

      {/* Plan mutation error */}
      {planMutation.isError && (
        <ErrorState
          heading="Dry run failed"
          message={planMutation.error instanceof Error ? planMutation.error.message : undefined}
          onRetry={() => planMutation.reset()}
          retryLabel="Dismiss"
        />
      )}

      {/* Run mutation error */}
      {runMutation.isError && (
        <ErrorState
          heading="Workflow execution failed"
          message={runMutation.error instanceof Error ? runMutation.error.message : undefined}
          onRetry={() => runMutation.reset()}
          retryLabel="Dismiss"
        />
      )}

      {/* Dry-run plan preview */}
      {planResult && !runMutation.isPending && (
        <WorkflowPlanPreview plan={planResult} />
      )}

      {/* Workflow execution result */}
      {runResult && (
        <div className="space-y-4 p-4 rounded-lg border border-border bg-surface" data-testid="workflow-result">
          {/* Metrics */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-text-primary">Result</span>
            <ExecutionMetricsBadge durationMs={runResult.total_duration_ms} />
          </div>

          {/* Timeline */}
          {runResult.steps.length > 0 && (
            <WorkflowTimeline steps={runResult.steps} />
          )}

          {/* AI response with full explainability */}
          <AIResponseCard
            content={runResult.answer}
            explanation={runResult.explanation}
            provider_used={runResult.provider_used}
            created_at={new Date().toISOString()}
            suggested_actions={runResult.suggested_actions}
            participating_agents={runResult.participating_agents}
            onSuggestedAction={handleSuggestedAction}
          />
        </div>
      )}
    </div>
  );
}
