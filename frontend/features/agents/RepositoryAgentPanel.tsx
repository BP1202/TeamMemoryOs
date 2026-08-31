/**
 * RepositoryAgentPanel — Repository Agent: question input, branch selector,
 * file history lookup, answer with commit summary list and full explainability.
 *
 * Architecture:
 *   - React Hook Form for form state.
 *   - useMutation for search and file history.
 *   - All AI responses show all 5 explainability fields.
 *
 * Security:
 *   - Suggested actions rendered as <button> only.
 *   - Stack trace / file paths are plain text — never rendered as HTML.
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import { UtilityIcons } from '@config/icons';
import { Button } from '@components/ui/Button';
import { Input } from '@components/ui/Input';
import { ErrorState } from '@components/feedback/ErrorState';
import { useAuthStore } from '@stores/authStore';
import { searchRepository, getFileHistory } from '@services/agentsService';
import { AIResponseCard } from '@features/chat/AIResponseCard';
import { BranchSelector } from './BranchSelector';
import { CommitSummaryList } from './CommitSummaryList';
import { ExecutionMetricsBadge } from './ExecutionMetricsBadge';
import type { RepositorySearchResponse, FileHistoryResponse } from '@typedefs/agents';

interface SearchFormValues {
  question: string;
  branch: string;
}

interface FileHistoryFormValues {
  file_path: string;
  branch: string;
}

export function RepositoryAgentPanel() {
  const orgId = useAuthStore((s) => s.user?.id ?? '');
  const [searchResult, setSearchResult] = useState<RepositorySearchResponse | null>(null);
  const [fileHistory, setFileHistory] = useState<FileHistoryResponse | null>(null);

  // ─── Search form ──────────────────────────────────────────────────────────
  const searchForm = useForm<SearchFormValues>({
    defaultValues: { question: '', branch: '' },
  });

  const searchMutation = useMutation({
    mutationFn: (values: SearchFormValues) =>
      searchRepository({
        organization_id: orgId,
        question: values.question,
        branch: values.branch || undefined,
      }),
    onSuccess: (data) => setSearchResult(data),
  });

  // ─── File history form ────────────────────────────────────────────────────
  const fileForm = useForm<FileHistoryFormValues>({
    defaultValues: { file_path: '', branch: '' },
  });

  const fileHistoryMutation = useMutation({
    mutationFn: (values: FileHistoryFormValues) =>
      getFileHistory({
        organization_id: orgId,
        file_path: values.file_path,
        branch: values.branch || undefined,
      }),
    onSuccess: (data) => setFileHistory(data),
  });

  const handleSuggestedAction = (action: string) => {
    searchForm.setValue('question', action);
    searchMutation.mutate({ ...searchForm.getValues(), question: action });
  };

  return (
    <div className="space-y-6" data-testid="repository-agent-panel">

      {/* ── Repository Search ───────────────────────────────────────────────── */}
      <section aria-labelledby="repo-search-heading" className="space-y-4">
        <h3 id="repo-search-heading" className="text-sm font-semibold text-text-primary">
          Repository Search
        </h3>

        <form
          onSubmit={searchForm.handleSubmit((v) => searchMutation.mutate(v))}
          className="space-y-3"
        >
          <div className="space-y-1">
            <label htmlFor="repo-question" className="text-xs font-medium text-text-secondary">
              Question
            </label>
            <Input
              id="repo-question"
              placeholder="What changed in the auth module last week?"
              aria-describedby={searchForm.formState.errors.question ? 'repo-question-error' : undefined}
              {...searchForm.register('question', { required: 'A question is required.' })}
            />
            {searchForm.formState.errors.question && (
              <p id="repo-question-error" className="text-xs text-danger" role="alert">
                {searchForm.formState.errors.question.message}
              </p>
            )}
          </div>

          <div className="space-y-1">
            <label htmlFor="branch-selector" className="text-xs font-medium text-text-secondary">
              Branch (optional)
            </label>
            <BranchSelector
              id="branch-selector"
              value={searchForm.watch('branch')}
              onChange={(branch) => searchForm.setValue('branch', branch)}
            />
          </div>

          <Button
            type="submit"
            variant="primary"
            size="sm"
            isLoading={searchMutation.isPending}
          >
            <UtilityIcons.Search className="h-3.5 w-3.5" aria-hidden="true" />
            Search Repository
          </Button>
        </form>

        {searchMutation.isError && (
          <ErrorState
            heading="Repository search failed"
            message={searchMutation.error instanceof Error ? searchMutation.error.message : undefined}
            onRetry={() => searchMutation.reset()}
            retryLabel="Dismiss"
          />
        )}

        {searchResult && (
          <div className="space-y-3" data-testid="repo-search-result">
            <AIResponseCard
              content={searchResult.answer}
              explanation={searchResult.explanation}
              provider_used={searchResult.provider_used}
              created_at={new Date().toISOString()}
              suggested_actions={searchResult.suggested_actions}
              onSuggestedAction={handleSuggestedAction}
            />

            {searchResult.commits.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
                  Related Commits ({searchResult.commits.length})
                </h4>
                <CommitSummaryList commits={searchResult.commits} />
              </div>
            )}
          </div>
        )}
      </section>

      <hr className="border-border" />

      {/* ── File History ────────────────────────────────────────────────────── */}
      <section aria-labelledby="file-history-heading" className="space-y-4">
        <h3 id="file-history-heading" className="text-sm font-semibold text-text-primary">
          File History
        </h3>

        <form
          onSubmit={fileForm.handleSubmit((v) => fileHistoryMutation.mutate(v))}
          className="space-y-3"
        >
          <div className="space-y-1">
            <label htmlFor="file-path" className="text-xs font-medium text-text-secondary">
              File path
            </label>
            <Input
              id="file-path"
              placeholder="backend/app/api/routes/auth.py"
              aria-describedby={fileForm.formState.errors.file_path ? 'file-path-error' : undefined}
              {...fileForm.register('file_path', { required: 'A file path is required.' })}
            />
            {fileForm.formState.errors.file_path && (
              <p id="file-path-error" className="text-xs text-danger" role="alert">
                {fileForm.formState.errors.file_path.message}
              </p>
            )}
          </div>

          <div className="space-y-1">
            <label htmlFor="file-branch-selector" className="text-xs font-medium text-text-secondary">
              Branch (optional)
            </label>
            <BranchSelector
              id="file-branch-selector"
              value={fileForm.watch('branch')}
              onChange={(branch) => fileForm.setValue('branch', branch)}
            />
          </div>

          <Button
            type="submit"
            variant="secondary"
            size="sm"
            isLoading={fileHistoryMutation.isPending}
          >
            <UtilityIcons.ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
            View File History
          </Button>
        </form>

        {fileHistoryMutation.isError && (
          <ErrorState
            heading="File history lookup failed"
            message={fileHistoryMutation.error instanceof Error ? fileHistoryMutation.error.message : undefined}
            onRetry={() => fileHistoryMutation.reset()}
            retryLabel="Dismiss"
          />
        )}

        {fileHistory && (
          <div className="space-y-2" data-testid="file-history-result">
            <div className="flex items-center gap-2">
              <code className="text-xs font-mono text-text-primary">{fileHistory.file_path}</code>
              <ExecutionMetricsBadge durationMs={null} />
              <span className="text-xs text-text-muted">on {fileHistory.branch}</span>
            </div>
            <CommitSummaryList commits={fileHistory.commits} />
          </div>
        )}
      </section>
    </div>
  );
}
