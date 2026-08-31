/**
 * Vitest + RTL global test setup.
 *
 * - Imports jest-dom matchers (toBeInTheDocument, etc.)
 * - Starts MSW server before tests, resets handlers after each, closes after all.
 * - Clears Zustand store state between tests.
 */

import '@testing-library/jest-dom';
import { afterAll, afterEach, beforeAll } from 'vitest';
import { cleanup } from '@testing-library/react';
import { server } from './mocks/server';

// jsdom does not implement scrollIntoView — polyfill for all tests.
window.HTMLElement.prototype.scrollIntoView = function () {};

// Start MSW
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));
afterEach(() => {
  server.resetHandlers();
  cleanup();
});
afterAll(() => server.close());
