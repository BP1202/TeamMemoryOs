/**
 * Axios client — singleton instance.
 * This is the ONLY place an Axios instance is created in the application.
 * All interceptors are registered in separate modules and imported here.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
});

export default apiClient;
