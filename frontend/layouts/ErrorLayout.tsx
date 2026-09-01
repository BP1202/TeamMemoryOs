/**
 * ErrorLayout — top-level error boundary page.
 * Shown when a route-level error is thrown (React Router errorElement).
 */

import { useRouteError, isRouteErrorResponse, Link } from 'react-router-dom';
import { StatusIcons } from '@config/icons';
import { Button } from '@components/ui/Button';

export function ErrorLayout() {
  const error = useRouteError();

  let heading = 'Something went wrong';
  let message = 'An unexpected error occurred.';

  if (isRouteErrorResponse(error)) {
    heading = `${error.status} — ${error.statusText}`;
    message = error.data?.message ?? message;
  } else if (error instanceof Error) {
    message = error.message;
  }

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center gap-6 bg-surface-base px-4"
      role="alert"
    >
      <StatusIcons.error className="h-12 w-12 text-danger" aria-hidden="true" />
      <div className="text-center space-y-1">
        <h1 className="text-xl font-semibold text-text-primary">{heading}</h1>
        <p className="text-sm text-text-secondary">{message}</p>
      </div>
      <Link to="/">
        <Button variant="secondary">Return to Dashboard</Button>
      </Link>
    </div>
  );
}
