/**
 * Auth service — POST /api/v1/auth/login
 *
 * Rules:
 *   - Uses application/x-www-form-urlencoded (OAuth2PasswordRequestForm).
 *   - Returns only the token; user profile fetched via userService.
 *   - Never logs or exposes the token.
 */

import { apiClient } from '@lib/api/client';
import type { LoginResponse } from '@typedefs/auth';

export async function loginUser(
  username: string,
  password: string,
): Promise<LoginResponse> {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);

  const { data } = await apiClient.post<LoginResponse>(
    '/api/v1/auth/login',
    params,
    { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
  );

  return data;
}
