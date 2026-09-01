import { apiClient } from './client';

/**
 * Creates and queues a new code submission.
 * @param {Object} data - { challenge: number, code: string, language?: string }
 */
export async function createSubmission(data) {
  return apiClient.post('submissions/', data);
}

/**
 * Retrieves the status and evaluation result of a specific submission.
 * @param {number|string} submissionId
 */
export async function getSubmission(submissionId) {
  return apiClient.get(`submissions/${submissionId}/`);
}

/**
 * Retrieves paginated list of submissions for current user with optional filters.
 * @param {Object} params - { challenge, status, page, page_size }
 */
export async function getSubmissions(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, value);
    }
  });
  const queryString = query.toString();
  const endpoint = queryString ? `submissions/?${queryString}` : 'submissions/';
  return apiClient.get(endpoint);
}

/**
 * Retrieves paginated submissions for current user for a specific challenge.
 * @param {number|string} challengeId
 * @param {Object} params - { page, page_size }
 */
export async function getChallengeSubmissions(challengeId, params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, value);
    }
  });
  const queryString = query.toString();
  const endpoint = queryString
    ? `challenges/${challengeId}/submissions/?${queryString}`
    : `challenges/${challengeId}/submissions/`;
  return apiClient.get(endpoint);
}

/**
 * Retrieves the current user's best score and attempt count across challenges.
 */
export async function getBestSubmissions() {
  return apiClient.get('submissions/best/');
}
