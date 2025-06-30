import React, { useState, useEffect } from 'react';
import './JobRecommendations.css';
import LoadingSpinner from '../common/LoadingSpinner';
import { fetchRecommendations as fetchRecommendationsApi, submitRecommendationFeedback } from '../../utils/apiConfig';

interface JobRecommendation {
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

interface JobRecommendationsProps {
  userId: string;
  token: string;
  apiBaseUrl: string;
}

const JobRecommendations: React.FC<JobRecommendationsProps> = ({ userId, token, apiBaseUrl }) => {
  const [recommendations, setRecommendations] = useState<JobRecommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [recommendationId, setRecommendationId] = useState<string>('');

  useEffect(() => {
    fetchRecommendations();
  }, [userId, token]);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);

      // Use hybrid API function that will automatically use mock data if needed
      const result = await fetchRecommendationsApi(token, userId, 5);
      
      if (result.error) {
        throw new Error(result.error);
      }
      
      if (result.data && result.data.status === 'success' && result.data.recommendations) {
        setRecommendations(result.data.recommendations);
        setRecommendationId(result.data.recommendation_id || `rec_${Date.now()}`);
      } else {
        setRecommendations([]);
        setError('No recommendations available');
      }
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch recommendations');
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRecommendationAction = async (jobId: string, actionType: string) => {
    try {
      // Record feedback about this recommendation using hybrid API function
      await submitRecommendationFeedback(token, recommendationId, jobId, actionType);

      // If user clicked or applied, highlight the recommendation
      if (actionType === 'clicked' || actionType === 'applied') {
        setRecommendations(prevRecs => 
          prevRecs.map(rec => 
            rec.job_id === jobId 
              ? { ...rec, highlighted: true } 
              : rec
          )
        );
      }

      // If user dismissed, remove from list
      if (actionType === 'ignored') {
        setRecommendations(prevRecs => 
          prevRecs.filter(rec => rec.job_id !== jobId)
        );
      }
    } catch (err) {
      console.error('Error recording recommendation feedback:', err);
    }
  };

  const renderMatchQuality = (score: number) => {
    let matchClass = 'match-low';
    if (score >= 0.7) matchClass = 'match-high';
    else if (score >= 0.4) matchClass = 'match-medium';
    
    return (
      <div className={`match-indicator ${matchClass}`}>
        <div className="match-bar" style={{ width: `${score * 100}%` }}></div>
        <span className="match-text">{Math.round(score * 100)}% Match</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="recommendations-loading">
        <LoadingSpinner size="medium" />
        <p>Finding the best jobs for you...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="recommendations-error">
        <p>Unable to load recommendations: {error}</p>
        <button onClick={fetchRecommendations} className="retry-button">
          Try Again
        </button>
      </div>
    );
  }

  if (recommendations.length === 0) {
    return (
      <div className="no-recommendations">
        <h3>No Job Recommendations</h3>
        <p>We don't have any personalized job recommendations for you at the moment.</p>
        <p>Complete your profile with more skills to get better matches!</p>
      </div>
    );
  }

  return (
    <div className="job-recommendations">
      <h2>Recommended for You</h2>
      <p className="recommendations-subtitle">
        Jobs that match your skills and preferences
      </p>
      
      <div className="recommendations-list">
        {recommendations.map(recommendation => (
          <div 
            key={recommendation.job_id} 
            className={`recommendation-card ${recommendation.highlighted ? 'highlighted' : ''}`}
          >
            <div className="recommendation-header">
              <h3>{recommendation.title}</h3>
              {renderMatchQuality(recommendation.relevance_score)}
            </div>
            
            <p className="recommendation-description">{recommendation.description}</p>
            
            <div className="recommendation-details">
              <div className="recommendation-budget">{recommendation.budget_range}</div>
              <div className="recommendation-deadline">Due: {recommendation.deadline}</div>
            </div>
            
            <div className="recommendation-skills">
              {recommendation.skills.map(skill => (
                <span key={skill} className="skill-tag">{skill}</span>
              ))}
            </div>
            
            <div className="recommendation-match-details">
              <div className="match-detail">
                <span className="match-label">Skills:</span>
                <div className="match-bar-container">
                  <div 
                    className="match-bar-fill" 
                    style={{ width: `${recommendation.match_reasons.skill_match * 100}%` }}
                  ></div>
                </div>
              </div>
              <div className="match-detail">
                <span className="match-label">Budget:</span>
                <div className="match-bar-container">
                  <div 
                    className="match-bar-fill" 
                    style={{ width: `${recommendation.match_reasons.budget_match * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
            
            <div className="recommendation-actions">
              <button 
                className="action-button apply"
                onClick={() => handleRecommendationAction(recommendation.job_id, 'applied')}
              >
                Apply Now
              </button>
              <button 
                className="action-button save"
                onClick={() => handleRecommendationAction(recommendation.job_id, 'saved')}
              >
                Save
              </button>
              <button 
                className="action-button dismiss"
                onClick={() => handleRecommendationAction(recommendation.job_id, 'ignored')}
              >
                Not Interested
              </button>
            </div>
          </div>
        ))}
      </div>
      
      <div className="recommendations-footer">
        <button onClick={fetchRecommendations} className="refresh-button">
          Refresh Recommendations
        </button>
      </div>
    </div>
  );
};

export default JobRecommendations;
