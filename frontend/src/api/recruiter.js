import { apiClient } from './client';

/**
 * Fetches the list of candidate engineering readiness summaries.
 * Supports query params: { search, min_skill_score, challenge_type }
 */
export async function getRecruiterCandidates(params = {}) {
  const query = new URLSearchParams();
  if (params.search && params.search.trim()) {
    query.append('search', params.search.trim());
  }
  if (params.min_skill_score !== undefined && params.min_skill_score !== null && params.min_skill_score !== '') {
    query.append('min_skill_score', params.min_skill_score);
  }
  if (params.challenge_type && params.challenge_type.trim()) {
    query.append('challenge_type', params.challenge_type.trim());
  }

  const qs = query.toString();
  const endpoint = qs ? `recruiter/candidates/?${qs}` : 'recruiter/candidates/';
  return apiClient.get(endpoint);
}

/**
 * Fetches detailed engineering assessment and challenge evidence for a candidate.
 */
export async function getRecruiterCandidate(username) {
  return apiClient.get(`recruiter/candidates/${encodeURIComponent(username)}/`);
}
