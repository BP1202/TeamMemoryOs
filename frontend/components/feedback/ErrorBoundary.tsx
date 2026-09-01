/**
 * ErrorBoundary — catches React render errors and shows a fallback UI.
 * Implements React class-based error boundary (no hooks equivalent).
 *
 * Accessibility: role="alert" on the fallback container.
 */

import { Component, type ReactNode, type ErrorInfo } from 'react';
import { StatusIcons } from '@config/icons';
import { Button } from '@components/ui/Button';

interface Props {
  children: ReactNode;
  /** Optional custom fallback. If omitted, renders the default error card. */
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // In production this would send to an error tracking service.
    // Never log sensitive auth data.
    console.error('[ErrorBoundary]', error.message, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div
          role="alert"
          aria-live="assertive"
          className="flex flex-col items-center justify-center gap-4 py-16 px-6 text-center"
        >
          <StatusIcons.error
            className="h-12 w-12 text-danger"
            aria-hidden="true"
          />
          <div className="space-y-1">
            <h2 className="text-base font-semibold text-text-primary">
              Something went wrong
            </h2>
            <p className="text-sm text-text-secondary max-w-sm">
              {this.state.error?.message ?? 'An unexpected error occurred.'}
            </p>
          </div>
          <Button variant="secondary" size="sm" onClick={this.handleReset}>
            Try again
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
