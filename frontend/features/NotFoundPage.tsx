/**
 * NotFoundPage — global 404 page.
 * Shown when the user navigates to an unmatched route.
 */

import { Link } from 'react-router-dom';
import { UtilityIcons } from '@config/icons';

export function NotFoundPage() {
  return (
    <div
      className="flex flex-col items-center justify-center min-h-screen gap-6 px-6 text-center"
      data-testid="not-found-page"
    >
      <div className="space-y-3">
        <p
          className="text-8xl font-bold text-text-muted select-none"
          aria-hidden="true"
        >
          404
        </p>
        <h1 className="text-xl font-semibold text-text-primary">
          Page not found
        </h1>
        <p className="text-sm text-text-secondary max-w-sm">
          The page you are looking for does not exist or has been moved.
        </p>
      </div>

      <Link
        to="/"
        aria-label="Back to Dashboard"
        className="inline-flex items-center justify-center gap-2 h-9 px-4 text-sm font-medium rounded-md
          bg-[var(--btn-primary-bg)] text-[var(--btn-primary-text)]
          hover:bg-[var(--btn-primary-bg-hover)] transition-colors
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
      >
        <UtilityIcons.ArrowRight className="h-4 w-4 rotate-180" aria-hidden="true" />
        Back to Dashboard
      </Link>
    </div>
  );
}
