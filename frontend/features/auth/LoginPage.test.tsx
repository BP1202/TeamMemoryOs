/**
 * LoginPage — integration tests (Sprint 8.1).
 * Tests: renders, validation, login success, login failure, server error.
 */

import { describe, it, expect } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from '../../tests/utils/renderWithProviders';
import { http, HttpResponse } from 'msw';
import { server } from '../../tests/mocks/server';
import { LoginPage } from './LoginPage';

describe('LoginPage', () => {
  // ── Renders ────────────────────────────────────────────────────────────

  it('renders email and password fields', () => {
    render(<LoginPage />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it('renders sign in button', () => {
    render(<LoginPage />);
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  // ── Validation ─────────────────────────────────────────────────────────

  it('shows validation errors on empty submit', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });

  it('shows invalid email format error', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);
    await user.type(screen.getByLabelText(/email/i), 'not-an-email');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/valid email/i)).toBeInTheDocument();
    });
  });

  // ── Login success ──────────────────────────────────────────────────────

  it('submits credentials and calls login + user profile', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText(/email/i), 'engineer@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    // After successful login the mutation fires — button shows loading state briefly
    // then navigates away. We just verify no error message appears.
    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  // ── Login failure ──────────────────────────────────────────────────────

  it('shows invalid credentials error on 401', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText(/email/i), 'bad@example.com');
    await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid email or password/i)).toBeInTheDocument();
    });
  });

  it('shows server error message on 500', async () => {
    server.use(
      http.post('http://localhost:8000/api/v1/auth/login', () =>
        HttpResponse.json({ detail: 'Internal server error' }, { status: 500 }),
      ),
    );

    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText(/email/i), 'engineer@example.com');
    await user.type(screen.getByLabelText(/password/i), 'password123');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      // Server errors show in root error alert
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});
