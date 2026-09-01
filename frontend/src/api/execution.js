import { apiClient } from './client';

/**
 * Executes code or multi-file repository in an isolated backend Docker container sandbox.
 * @param {Object} data - { code?: string, files?: Object, entrypoint?: string, language?: string, stdin?: string, timeout?: number }
 */
export async function runCode(data) {
  return apiClient.post('execution/run/', data);
}
