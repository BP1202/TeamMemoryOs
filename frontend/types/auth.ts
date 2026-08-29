/**
 * Authentication and user identity types.
 * Field names mirror backend JWT payload and User schema exactly.
 *
 * Backend ref:
 *   - schemas/auth.py  → Token
 *   - schemas/user.py  → UserRead
 *   - POST /api/v1/auth/login  → OAuth2PasswordRequestForm → Token
 *   - GET  /api/v1/users/me   → UserRead
 */

// ─── User ──────────────────────────────────────────────────────────────────
// Mirrors backend UserRead schema exactly.

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ─── Auth API ──────────────────────────────────────────────────────────────

/**
 * Login request — sent as application/x-www-form-urlencoded.
 * Backend uses OAuth2PasswordRequestForm: field is `username` (maps to email).
 */
export interface LoginRequest {
  username: string; // email address — OAuth2 convention
  password: string;
}

/**
 * Token response from POST /api/v1/auth/login.
 * User details are fetched separately from GET /api/v1/users/me.
 */
export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
}

// ─── Auth store state ──────────────────────────────────────────────────────

export interface AuthState {
  token: string | null;
  user: User | null;
  organization_id: string | null;
  isAuthenticated: boolean;
}
