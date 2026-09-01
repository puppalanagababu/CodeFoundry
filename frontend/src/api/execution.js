import { apiClient } from './client';

/**
 * Executes code in an isolated backend Docker container sandbox.
 * @param {Object} data - { code: string, language?: string, stdin?: string, timeout?: number }
 */
export async function runCode(data) {
  return apiClient.post('execution/run/', data);
}
