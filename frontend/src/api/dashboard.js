import { apiClient } from './client';

/**
 * Fetches the dashboard overview, recent submissions, and difficulty progress for current user.
 */
export async function getDashboard() {
  return apiClient.get('dashboard/');
}
