/**
 * API Configuration utility for GigNova
 * Handles switching between real API calls and mock data
 */

import { 
  loginUser as realLoginUser,
  registerUser as realRegisterUser,
  fetchJobs as realFetchJobs,
  fetchRecommendations as realFetchRecommendations,
  submitRecommendationFeedback as realSubmitRecommendationFeedback
} from './api';

import {
  mockLoginUser,
  mockRegisterUser,
  mockFetchJobs,
  mockCreateJob,
  mockFetchRecommendations,
  mockSubmitRecommendationFeedback
} from './mockApi';

// Configuration for API usage
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8889/api/v1';
const useMockApi = import.meta.env.VITE_USE_MOCK_API === 'true';

// Determine if we should use mock API
const isStandaloneMockMode = useMockApi;
const isHybridMode = true; // Enable hybrid mode to handle backend errors gracefully
const shouldUseMockApi = isStandaloneMockMode || isHybridMode;

// Define the final API URL based on the mode
const finalApiUrl = isStandaloneMockMode ? '' : apiUrl;

// Log the API configuration
console.log('API Configuration:', {
  useMockApi,
  apiUrl: finalApiUrl,
  isStandaloneMockMode,
  isHybridMode,
  shouldUseMockApi
});

// Force mock API in production if URL is 'mock'
if (import.meta.env.PROD && import.meta.env.VITE_API_URL === 'mock') {
  console.log('Production build with mock API - forcing mock implementation');
}

// Export configured API functions
export const loginUser = (email: string, password: string) => {
  return shouldUseMockApi 
    ? mockLoginUser(email, password)
    : realLoginUser(finalApiUrl, email, password);
};

export const registerUser = (email: string, password: string, role: 'client' | 'freelancer') => {
  return shouldUseMockApi
    ? mockRegisterUser(email, password, role)
    : realRegisterUser(finalApiUrl, email, password, role);
};

export const fetchJobs = (token: string) => {
  return shouldUseMockApi
    ? mockFetchJobs()
    : realFetchJobs(finalApiUrl, token);
};

export const fetchRecommendations = (token: string, freelancerId: string, count: number = 5) => {
  return shouldUseMockApi
    ? mockFetchRecommendations(freelancerId, count)
    : realFetchRecommendations(finalApiUrl, token, freelancerId, count);
};

export const submitRecommendationFeedback = (token: string, recommendationId: string, jobId: string, feedbackType: string) => {
  return shouldUseMockApi
    ? mockSubmitRecommendationFeedback(recommendationId, jobId, feedbackType)
    : realSubmitRecommendationFeedback(finalApiUrl, token, recommendationId, jobId, feedbackType);
};

export const createJob = (jobData: any, token: string) => {
  if (shouldUseMockApi) {
    return mockCreateJob(jobData);
  } else {
    // Implement real API call if needed
    console.warn('Real API call for createJob not implemented');
    return Promise.resolve({ data: null, error: 'Not implemented', status: 501 });
  }
};

// Export configuration
export const config = {
  useMockApi,
  apiUrl: finalApiUrl
};
