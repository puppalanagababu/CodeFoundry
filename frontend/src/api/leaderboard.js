import { apiClient } from './client';

/**
 * Fetches the developer leaderboard rankings.
 */
export async function getLeaderboard() {
  return apiClient.get('leaderboard/');
}
