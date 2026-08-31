/**
 * Chat service — wraps POST /api/v1/chat/ask.
 *
 * Rules:
 *   - Only this file calls the chat endpoint.
 *   - No components or stores import from axios directly.
 *   - AbortController signal passed for cancellation support.
 */

import { apiClient } from '@lib/api/client';
import type { ChatAskRequest, ChatAskResponse } from '@typedefs/chat';

/**
 * Send a question to the Granite-powered RAG chat endpoint.
 *
 * @param request - The request payload including question and options.
 * @param signal  - Optional AbortController signal for query cancellation.
 * @returns The AI-generated answer with explanation and citations.
 */
export async function askChat(
  request: ChatAskRequest,
  signal?: AbortSignal,
): Promise<ChatAskResponse> {
  const response = await apiClient.post<ChatAskResponse>(
    '/api/v1/chat/ask',
    request,
    { signal },
  );
  return response.data;
}
