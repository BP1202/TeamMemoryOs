/**
 * CreateScenarioDialog — modal dialog for creating a new scenario.
 *
 * Rules:
 *   - Form state via React Hook Form.
 *   - Submission via useMutation, invalidates scenario list on success.
 *   - Focus trap and ESC close from Dialog primitive.
 */

import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@components/ui/Dialog';
import { Input } from '@components/ui/Input';
import { Button } from '@components/ui/Button';
import { useAuthStore } from '@stores/authStore';
import { createScenario } from '@services/scenarioService';
import { SCENARIO_LIST_KEY } from './ScenarioList';
import type { ScenarioCreate } from '@typedefs/memory';

// ─── Form fields ───────────────────────────────────────────────────────────

interface CreateScenarioForm {
  name: string;
  description: string;
}

// ─── Props ─────────────────────────────────────────────────────────────────

interface CreateScenarioDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// ─── Component ─────────────────────────────────────────────────────────────

export function CreateScenarioDialog({
  open,
  onOpenChange,
}: CreateScenarioDialogProps) {
  const queryClient = useQueryClient();
  const orgId       = useAuthStore((s) => s.user?.id ?? '');

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateScenarioForm>({
    defaultValues: { name: '', description: '' },
  });

  const mutation = useMutation({
    mutationFn: (data: CreateScenarioForm) => {
      const payload: ScenarioCreate = {
        organization_id: orgId,
        name:            data.name,
        description:     data.description || undefined,
        is_active:       true,
      };
      return createScenario(payload);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: SCENARIO_LIST_KEY(orgId) });
      reset();
      onOpenChange(false);
    },
  });

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen) {
      reset();
      mutation.reset();
    }
    onOpenChange(nextOpen);
  };

  const onSubmit = handleSubmit((data) => {
    mutation.mutate(data);
  });

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent aria-labelledby="create-scenario-title">
        <DialogTitle id="create-scenario-title">New Scenario</DialogTitle>
        <DialogDescription>
          Group related memory entries under a scenario for easier filtering.
        </DialogDescription>

        {/* eslint-disable-next-line @typescript-eslint/no-misused-promises */}
        <form onSubmit={onSubmit} id="create-scenario-form" noValidate>
          <div className="space-y-4">
            {/* Name */}
            <Input
              id="scenario-name"
              label="Name"
              placeholder="e.g. Q4 Infrastructure Migration"
              aria-required="true"
              error={errors.name?.message}
              {...register('name', {
                required: 'Name is required',
                maxLength: { value: 255, message: 'Max 255 characters' },
              })}
            />

            {/* Description */}
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="scenario-description"
                className="text-sm font-medium text-text-secondary"
              >
                Description
              </label>
              <textarea
                id="scenario-description"
                rows={3}
                placeholder="Optional description…"
                className="w-full rounded-md text-sm bg-[var(--input-bg)] text-[var(--input-text)] border border-[var(--input-border)] px-[var(--input-padding-x)] py-[var(--input-padding-y)] focus:outline-none focus:border-[var(--input-focus-border)] focus:ring-2 focus:ring-[var(--input-focus-ring)] resize-y"
                {...register('description')}
              />
            </div>

            {/* Mutation error */}
            {mutation.isError && (
              <p role="alert" className="text-sm text-danger">
                Failed to create scenario. Please try again.
              </p>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => handleOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              form="create-scenario-form"
              isLoading={isSubmitting || mutation.isPending}
              disabled={isSubmitting || mutation.isPending}
            >
              Create scenario
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
