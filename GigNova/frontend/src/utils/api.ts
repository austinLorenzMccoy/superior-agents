/**
 * API utility functions for GigNova
 */

interface ApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: any;
  token?: string;
  headers?: Record<string, string>;
}

interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  status: number;
}

// Auth response types
export interface AuthResponse {
  access_token: string;
  user_id: string;
  role: 'client' | 'freelancer';
  token_type: string;
}

// Job types
export interface Job {
  job_id: string;
  title: string;
  description: string;
  skills: string[];
  budget_min: number;
  budget_max: number;
  deadline: string;
  status: 'posted' | 'in_progress' | 'completed';
  client_id: string;
  freelancer_id?: string;
}

// Recommendation types
export interface JobRecommendation {
  job_id: string;
  title: string;
  description: string;
  skills: string[];
  budget_range: string;
  deadline: string;
  relevance_score: number;
  match_reasons: {
    skill_match: number;
    preference_match: number;
    budget_match: number;
  };
  highlighted?: boolean;
}

export interface RecommendationResponse {
  status: string;
  recommendation_id: string;
  recommendations: JobRecommendation[];
}

/**
 * Fetch data from the API with proper error handling
 * @param endpoint API endpoint to fetch from
 * @param options Request options
 * @returns Promise with data, error, and status
 */
export const fetchApi = async <T>(
  baseUrl: string,
  endpoint: string, 
  options: ApiOptions = {}
): Promise<ApiResponse<T>> => {
  // If baseUrl is empty or 'mock', we should not make an actual HTTP request
  if (!baseUrl || baseUrl === 'mock') {
    console.error('Attempted to make HTTP request with invalid URL. This should be handled by mockApi functions.');
    return {
      data: null,
      error: 'Invalid API URL. This should be handled by mockApi functions.',
      status: 500
    };
  }
  const { 
    method = 'GET', 
    body, 
    token, 
    headers = {} 
  } = options;

  try {
    // Get auth token from localStorage if available
    const authData = localStorage.getItem('authData');
    let tokenFromStorage = null;
    if (authData) {
      try {
        const parsedAuthData = JSON.parse(authData);
        tokenFromStorage = parsedAuthData.token;
      } catch (e) {
        console.warn('Failed to parse auth data from localStorage');
      }
    }

    const requestHeaders: HeadersInit = {
      'Content-Type': 'application/json',
      ...headers
    };

    // Add authorization header if token exists
    if (token || tokenFromStorage) {
      requestHeaders['Authorization'] = `Bearer ${token || tokenFromStorage}`;
    }

    console.log(`Making ${method} request to ${baseUrl}/${endpoint}`, body);
    
    const response = await fetch(`${baseUrl}/${endpoint}`, {
      method,
      headers: requestHeaders,
      body: body ? JSON.stringify(body) : undefined,
      mode: 'cors',
      credentials: 'include'
    });

    console.log(`Response status: ${response.status}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API error: ${response.status} ${errorText}`);
      return { data: null, error: errorText || 'Unknown error', status: response.status };
    }

    let data;
    try {
      data = await response.json();
      console.log('Response data:', data);
    } catch (e) {
      console.error('Error parsing JSON response:', e);
      data = null;
    }

    return {
      data,
      error: null,
      status: response.status
    };
  } catch (error) {
    console.error('API request failed:', error);
    return {
      data: null,
      error: error instanceof Error ? error.message : 'Network error',
      status: 0
    };
  }
};

/**
 * Login user with email and password
 * @param baseUrl API base URL
 * @param email User email
 * @param password User password
 * @returns Promise with login response
 */
export const loginUser = async (
  baseUrl: string,
  email: string,
  password: string
): Promise<ApiResponse<AuthResponse>> => {
  return fetchApi<AuthResponse>(baseUrl, 'auth/login', {
    method: 'POST',
    body: {
      username: email,
      password
    }
  });
};

/**
 * Register a new user
 * @param baseUrl API base URL
 * @param email User email
 * @param password User password
 * @param role User role (client or freelancer)
 * @returns Promise with registration response
 */
export const registerUser = async (
  baseUrl: string,
  email: string,
  password: string,
  role: 'client' | 'freelancer'
): Promise<ApiResponse<AuthResponse>> => {
  return fetchApi<AuthResponse>(baseUrl, 'auth/register', {
    method: 'POST',
    body: {
      username: email,
      password,
      role
    }
  });
};

/**
 * Fetch jobs with authentication
 * @param baseUrl API base URL
 * @param token Authentication token
 * @returns Promise with jobs response
 */
export const fetchJobs = async (
  baseUrl: string,
  token: string
): Promise<ApiResponse<Job[]>> => {
  return fetchApi<Job[]>(baseUrl, 'jobs', {
    method: 'GET',
    token
  });
};

/**
 * Fetch personalized job recommendations for a freelancer
 * @param baseUrl API base URL
 * @param token Authentication token
 * @param freelancerId ID of the freelancer
 * @param count Number of recommendations to fetch
 * @returns Promise with recommendations response
 */
export const fetchRecommendations = async (
  baseUrl: string,
  token: string,
  freelancerId: string,
  count: number = 5
): Promise<ApiResponse<RecommendationResponse>> => {
  return fetchApi<RecommendationResponse>(baseUrl, 'recommendations', {
    method: 'POST',
    token,
    body: {
      freelancer_id: freelancerId,
      count
    }
  });
};

/**
 * Submit feedback for a job recommendation
 * @param baseUrl API base URL
 * @param token Authentication token
 * @param recommendationId ID of the recommendation set
 * @param jobId ID of the job that received feedback
 * @param feedbackType Type of feedback (clicked, applied, ignored, etc.)
 * @returns Promise with feedback submission response
 */
export const submitRecommendationFeedback = async (
  baseUrl: string,
  token: string,
  recommendationId: string,
  jobId: string,
  feedbackType: string
): Promise<ApiResponse<any>> => {
  return fetchApi<any>(baseUrl, 'recommendations/feedback', {
    method: 'POST',
    token,
    body: {
      recommendation_id: recommendationId,
      job_id: jobId,
      feedback_type: feedbackType
    }
  });
};
