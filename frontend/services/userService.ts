/**
 * User service — /api/v1/users
 *
 * GET /api/v1/users/me — fetch the currently authenticated user.
 */

import { apiClient } from '@lib/api/client';
import type { User } from '@typedefs/auth';

export async function getCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>('/api/v1/users/me');
  return data;
}
