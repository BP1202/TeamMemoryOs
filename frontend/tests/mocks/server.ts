/**
 * MSW service worker setup for tests (Node environment).
 */

import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
