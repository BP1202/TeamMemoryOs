/**
 * LoginPage — authentication page.
 *
 * Wires the login form to POST /api/v1/auth/login via React Query mutation.
 * On success: stores token, fetches user profile, redirects to the originally
 * intended destination (or dashboard).
 */

import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@stores/authStore';
import { loginUser } from '@services/authService';
import { getCurrentUser } from '@services/userService';
import { CURRENT_USER_KEY } from '@hooks/useCurrentUser';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@components/ui/Card';
import { Input } from '@components/ui/Input';
import { Button } from '@components/ui/Button';
import { normalizeError } from '@lib/api/errors';

interface LoginFormValues {
  email: string;
  password: string;
}

export function LoginPage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const setAuth         = useAuthStore((s) => s.setAuth);
  const navigate        = useNavigate();
  const location        = useLocation();
  const queryClient     = useQueryClient();

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname ?? '/';

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) navigate(from, { replace: true });
  }, [isAuthenticated, navigate, from]);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>();

  const loginMutation = useMutation({
    mutationFn: ({ email, password }: LoginFormValues) =>
      loginUser(email, password),

    onSuccess: async (data) => {
      // Store token first so subsequent requests are authorized
      // User will be fully set after profile fetch
      const user = await getCurrentUser();
      setAuth(data.access_token, user);
      // Seed the query cache so useCurrentUser doesn't re-fetch immediately
      queryClient.setQueryData(CURRENT_USER_KEY, user);
      navigate(from, { replace: true });
    },

    onError: (error: unknown) => {
      const apiError = normalizeError(error);
      if (apiError.status === 401) {
        setError('password', {
          type: 'manual',
          message: 'Invalid email or password',
        });
      } else {
        setError('root', {
          type: 'manual',
          message: apiError.message,
        });
      }
    },
  });

  const onSubmit = (values: LoginFormValues) => {
    loginMutation.mutate(values);
  };

  return (
    <Card variant="elevated" aria-labelledby="login-title">
      <CardHeader>
        <CardTitle id="login-title">Sign in</CardTitle>
        <CardDescription>Enter your credentials to access TeamMemoryOS</CardDescription>
      </CardHeader>

      <CardContent>
        <form
          onSubmit={handleSubmit(onSubmit)}
          noValidate
          aria-label="Sign in form"
          className="space-y-4"
        >
          {/* Root-level server error (non-401) */}
          {errors.root && (
            <div
              role="alert"
              className="text-sm text-danger bg-danger-subtle border border-danger rounded-md px-3 py-2"
            >
              {errors.root.message}
            </div>
          )}

          <Input
            label="Email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            error={errors.email?.message}
            {...register('email', {
              required: 'Email is required',
              pattern: {
                value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                message: 'Enter a valid email address',
              },
            })}
          />

          <Input
            label="Password"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            error={errors.password?.message}
            {...register('password', {
              required: 'Password is required',
              minLength: { value: 8, message: 'Password must be at least 8 characters' },
            })}
          />

          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full"
            isLoading={isSubmitting || loginMutation.isPending}
          >
            Sign in
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
