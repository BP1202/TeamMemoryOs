/**
 * Authentication and user identity types.
 * Field names mirror backend JWT payload and User schema exactly.
 */

// ─── User ──────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  organization_id: string;
  is_active: boolean;
  created_at: string;
}

export type UserRole = 'admin' | 'member' | 'viewer';

// ─── Auth API responses ────────────────────────────────────────────────────

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
  user: User;
}

// ─── Auth store state ──────────────────────────────────────────────────────

export interface AuthState {
  token: string | null;
  user: User | null;
  organization_id: string | null;
  isAuthenticated: boolean;
}
