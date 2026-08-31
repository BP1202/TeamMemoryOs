/**
 * CreateMemoryDrawer — slide-in form for creating a new memory entry.
 *
 * Rules:
 *   - Form state via React Hook Form.
 *   - Submission via useMutation, invalidates memory list on success.
 *   - Closes on success or ESC.
 */

import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
  DrawerBody,
  DrawerFooter,
} from '@components/ui/Drawer';
import { Input } from '@components/ui/Input';
import { Button } from '@components/ui/Button';
import { useMemoryStore } from '@stores/memoryStore';
import { useAuthStore } from '@stores/authStore';
import { createMemoryEntry } from '@services/memoryService';
import { MEMORY_TYPES, MEMORY_TYPE_LABELS } from '@typedefs/memory';
import type { MemoryType, MemoryEntryCreate } from '@typedefs/memory';

// ─── Query invalidation key ────────────────────────────────────────────────

export const MEMORY_LIST_KEY = (orgId: string) =>
  ['memory', 'list', orgId] as const;

// ─── Form fields ───────────────────────────────────────────────────────────

interface CreateMemoryForm {
  title: string;
  content: string;
  memory_type: MemoryType;
}

// ─── Component ─────────────────────────────────────────────────────────────

export function CreateMemoryDrawer() {
  const queryClient = useQueryClient();
  const isOpen      = useMemoryStore((s) => s.isCreateDrawerOpen);
  const closeDrawer = useMemoryStore((s) => s.closeCreateDrawer);
  const orgId       = useAuthStore((s) => s.user?.id ?? '');   // org injected via interceptor

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateMemoryForm>({
    defaultValues: { title: '', content: '', memory_type: 'decision' },
  });

  const mutation = useMutation({
    mutationFn: (data: CreateMemoryForm) => {
      const payload: MemoryEntryCreate = {
        organization_id: orgId,
        memory_type:     data.memory_type,
        title:           data.title || undefined,
        content:         data.content,
      };
      return createMemoryEntry(payload);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['memory', 'list'] });
      reset();
      closeDrawer();
    },
  });

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      reset();
      closeDrawer();
    }
  };

  const onSubmit = handleSubmit((data) => {
    mutation.mutate(data);
  });

  return (
    <Drawer open={isOpen} onOpenChange={handleOpenChange}>
      <DrawerContent size="md" aria-labelledby="create-memory-title">
        <DrawerHeader>
          <DrawerTitle id="create-memory-title">New Memory Entry</DrawerTitle>
          <DrawerDescription>
            Capture a decision, context, artifact, insight, or discussion.
          </DrawerDescription>
        </DrawerHeader>

        {/* eslint-disable-next-line @typescript-eslint/no-misused-promises */}
        <form onSubmit={onSubmit} id="create-memory-form" noValidate>
          <DrawerBody>
            <div className="space-y-5">
              {/* Title */}
              <Input
                id="create-memory-title-input"
                label="Title"
                placeholder="Short summary (optional)"
                aria-describedby={errors.title ? 'create-memory-title-error' : undefined}
                {...register('title', { maxLength: { value: 255, message: 'Max 255 characters' } })}
                error={errors.title?.message}
              />

              {/* Memory type */}
              <div className="flex flex-col gap-1.5">
                <label
                  htmlFor="create-memory-type"
                  className="text-sm font-medium text-text-secondary"
                >
                  Type
                </label>
                <select
                  id="create-memory-type"
                  className="w-full rounded-md text-sm bg-[var(--input-bg)] text-[var(--input-text)] border border-[var(--input-border)] px-[var(--input-padding-x)] py-[var(--input-padding-y)] focus:outline-none focus:border-[var(--input-focus-border)] focus:ring-2 focus:ring-[var(--input-focus-ring)]"
                  {...register('memory_type', { required: 'Type is required' })}
                  aria-describedby={errors.memory_type ? 'create-memory-type-error' : undefined}
                >
                  {MEMORY_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {MEMORY_TYPE_LABELS[t]}
                    </option>
                  ))}
                </select>
                {errors.memory_type && (
                  <p
                    id="create-memory-type-error"
                    role="alert"
                    className="text-xs text-[var(--input-error-label)]"
                  >
                    {errors.memory_type.message}
                  </p>
                )}
              </div>

              {/* Content */}
              <div className="flex flex-col gap-1.5">
                <label
                  htmlFor="create-memory-content"
                  className="text-sm font-medium text-text-secondary"
                >
                  Content <span aria-hidden="true" className="text-danger">*</span>
                </label>
                <textarea
                  id="create-memory-content"
                  rows={8}
                  placeholder="Enter the memory content…"
                  className="w-full rounded-md text-sm bg-[var(--input-bg)] text-[var(--input-text)] border border-[var(--input-border)] px-[var(--input-padding-x)] py-[var(--input-padding-y)] focus:outline-none focus:border-[var(--input-focus-border)] focus:ring-2 focus:ring-[var(--input-focus-ring)] resize-y"
                  aria-required="true"
                  aria-describedby={errors.content ? 'create-memory-content-error' : undefined}
                  aria-invalid={errors.content ? 'true' : undefined}
                  {...register('content', {
                    required: 'Content is required',
                    minLength: { value: 1, message: 'Content cannot be empty' },
                  })}
                />
                {errors.content && (
                  <p
                    id="create-memory-content-error"
                    role="alert"
                    className="text-xs text-[var(--input-error-label)]"
                  >
                    {errors.content.message}
                  </p>
                )}
              </div>

              {/* Mutation error */}
              {mutation.isError && (
                <p role="alert" className="text-sm text-danger">
                  Failed to create memory entry. Please try again.
                </p>
              )}
            </div>
          </DrawerBody>

          <DrawerFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => handleOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              form="create-memory-form"
              isLoading={isSubmitting || mutation.isPending}
              disabled={isSubmitting || mutation.isPending}
            >
              Save memory
            </Button>
          </DrawerFooter>
        </form>
      </DrawerContent>
    </Drawer>
  );
}
