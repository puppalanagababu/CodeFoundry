import { apiClient } from './client';

/**
 * Fetches the public developer profile for the given username.
 */
export async function getPublicProfile(username) {
  return apiClient.get(`users/profile/${encodeURIComponent(username)}/`);
}
