import { apiClient } from './client';

/**
 * Fetches challenges with optional filtering, search, and pagination.
 * @param {Object} params - Query params (search, difficulty, challenge_type, programming_language, page, page_size)
 */
export async function getChallenges(params = {}) {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, value);
    }
  });

  const queryString = query.toString();
  const endpoint = queryString ? `challenges/?${queryString}` : 'challenges/';
  return apiClient.get(endpoint);
}

/**
 * Fetches details for a specific challenge by ID.
 * @param {number|string} id - Challenge ID
 */
export async function getChallenge(id) {
  return apiClient.get(`challenges/${id}/`);
}

/**
 * Fetches overall challenge progress and per-challenge attempt summary for current user.
 */
export async function getChallengeProgress() {
  return apiClient.get('challenges/progress/');
}

