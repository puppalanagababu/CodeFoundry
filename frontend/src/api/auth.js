import { apiClient } from './client';

/**
 * Registers a new student user.
 * @param {Object} data - { username, email, password, password2 }
 */
export async function registerUser(data) {
  return apiClient.post('auth/register/', data);
}

/**
 * Logs in a user and retrieves JWT tokens + user profile.
 * @param {Object} data - { username, password }
 */
export async function loginUser(data) {
  return apiClient.post('auth/login/', data);
}

/**
 * Refreshes an access token using a refresh token.
 * @param {string} refresh - The refresh token
 */
export async function refreshToken(refresh) {
  return apiClient.post('auth/refresh/', { refresh });
}

/**
 * Fetches the currently authenticated user's profile.
 */
export async function getCurrentUser() {
  return apiClient.get('auth/me/');
}
