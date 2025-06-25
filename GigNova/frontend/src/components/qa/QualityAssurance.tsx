import React, { useState, useEffect } from 'react';
import './QualityAssurance.css';

interface QAProps {
  jobId: string;
  deliverableId?: string;
}

interface Job {
  job_id: string;
  title: string;
  description?: string;
  skills?: string[];
  budget_min?: number;
  budget_max?: number;
}

const QualityAssurance: React.FC<QAProps> = ({ jobId, deliverableId }) => {
  const [ratings, setRatings] = useState<Record<string, number>>({
    quality: 0,
    accuracy: 0,
    timeliness: 0,
    communication: 0,
    professionalism: 0
  });
  
  const [feedback, setFeedback] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [qaScore, setQaScore] = useState<number>(0);
  const [jobDetails, setJobDetails] = useState<Job | null>(null);
  
  const criteria = [
    { id: 'quality', name: 'Quality of Work', description: 'Overall quality and craftsmanship of the deliverable' },
    { id: 'accuracy', name: 'Accuracy', description: 'How well the work matches the requirements' },
    { id: 'timeliness', name: 'Timeliness', description: 'Delivery within the agreed timeframe' },
    { id: 'communication', name: 'Communication', description: 'Responsiveness and clarity of communication' },
    { id: 'professionalism', name: 'Professionalism', description: 'Professional conduct throughout the project' }
  ];
  
  // Fetch job details when jobId changes
  useEffect(() => {
    const fetchJobDetails = async () => {
      try {
        // In a real app, this would be an API call
        // For now, we'll use the jobs from App.tsx
        const mockJobs = [
          {
            job_id: "job-1",
            title: "Website Development",
            description: "Create a responsive website for a small business",
            skills: ["React", "Node.js", "MongoDB", "AWS", "TypeScript"],
            budget_min: 1500,
            budget_max: 3000,
          },
          {
            job_id: "job-2",
            title: "Mobile App Design",
            description: "Design UI/UX for a fitness tracking app",
            skills: ["Figma", "UI/UX", "Swift", "Kotlin", "Adobe XD"],
            budget_min: 2000,
            budget_max: 4500,
          },
          {
            job_id: "job-3",
            title: "Smart Contract Development",
            description: "Develop Ethereum smart contracts for an NFT marketplace",
            skills: ["Solidity", "Blockchain", "Ethereum"],
            budget_min: 1200,
            budget_max: 2500,
          },
          {
            job_id: "job-4",
            title: "E-commerce Platform Development",
            description: "Build a custom e-commerce platform with payment integration",
            skills: ["Shopify", "WooCommerce", "PHP", "JavaScript", "Payment Integration"],
            budget_min: 5000,
            budget_max: 12000,
          },
          {
            job_id: "job-5",
            title: "Content Writing for Tech Blog",
            description: "Create technical articles for a software development blog",
            skills: ["Technical Writing", "SEO", "Research", "Editing"],
            budget_min: 500,
            budget_max: 1200,
          },
          {
            job_id: "job-6",
            title: "AI Model Training",
            description: "Train and optimize machine learning models for image recognition",
            skills: ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Data Science"],
            budget_min: 3000,
            budget_max: 8000,
          }
        ];
        
        const job = mockJobs.find(j => j.job_id === jobId);
        
        if (job) {
          setJobDetails(job);
        } else {
          console.error(`Job with ID ${jobId} not found`);
        }
      } catch (error) {
        console.error('Error fetching job details:', error);
      }
    };
    
    if (jobId) {
      fetchJobDetails();
    }
  }, [jobId]);
  
  const handleRatingChange = (criteriaId: string, value: number) => {
    setRatings({...ratings, [criteriaId]: value});
  };
  
  const calculateOverallScore = () => {
    const values = Object.values(ratings);
    return values.reduce((sum, val) => sum + val, 0) / values.length;
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setLoading(true);
    
    // Calculate overall score
    const score = calculateOverallScore();
    setQaScore(score);
    
    // Mock API call
    setTimeout(() => {
      console.log('QA assessment submitted:', {
        jobId,
        jobTitle: jobDetails?.title,
        deliverableId,
        ratings,
        overallScore: score,
        feedback
      });
      setLoading(false);
      setSubmitted(true);
    }, 1500);
  };
  
  if (submitted) {
    return (
      <div className="qa-container">
        <div className="qa-success">
          <h3>Quality Assessment Submitted</h3>
          <div className="qa-score">
            <div className="score-circle">
              <span>{qaScore?.toFixed(1)}</span>
              <small>/5</small>
            </div>
          </div>
          <p>Thank you for your assessment of {jobDetails?.title || `Job #${jobId}`}.</p>
          <p>The freelancer has been notified.</p>
          <button 
            className="reset-button"
            onClick={() => {
              setRatings({
                quality: 0,
                accuracy: 0,
                timeliness: 0,
                communication: 0,
                professionalism: 0
              });
              setFeedback('');
              setSubmitted(false);
            }}
          >
            Submit Another Assessment
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="qa-container">
      <h2>Quality Assurance Assessment</h2>
      
      {jobDetails ? (
        <div className="job-details-header">
          <h3>{jobDetails.title}</h3>
          {jobDetails.description && <p className="job-description">{jobDetails.description}</p>}
          {jobDetails.skills && jobDetails.skills.length > 0 && (
            <div className="job-skills">
              {jobDetails.skills.map((skill, index) => (
                <span key={index} className="skill-tag">{skill}</span>
              ))}
            </div>
          )}
          {(jobDetails.budget_min || jobDetails.budget_max) && (
            <p className="job-budget">
              Budget: ${jobDetails.budget_min} - ${jobDetails.budget_max}
            </p>
          )}
        </div>
      ) : (
        <p className="loading-job">Loading job details...</p>
      )}
      
      <p className="qa-description">
        Evaluate the quality of the delivered work based on the following criteria.
        Rate each aspect from 1 (poor) to 5 (excellent).
      </p>
      
      <form onSubmit={handleSubmit}>
        <div className="criteria-list">
          {criteria.map(criterion => (
            <div key={criterion.id} className="criterion">
              <div className="criterion-header">
                <h4>{criterion.name}</h4>
                <div className="rating-display">{ratings[criterion.id]}/5</div>
              </div>
              <p className="criterion-description">{criterion.description}</p>
              <div className="rating-input">
                {[1, 2, 3, 4, 5].map(value => (
                  <label key={value} className={ratings[criterion.id] === value ? 'selected' : ''}>
                    <input
                      type="radio"
                      name={`rating-${criterion.id}`}
                      value={value}
                      checked={ratings[criterion.id] === value}
                      onChange={() => handleRatingChange(criterion.id, value)}
                    />
                    {value}
                  </label>
                ))}
              </div>
            </div>
          ))}
        </div>
        
        <div className="feedback-section">
          <label htmlFor="feedback">Additional Feedback:</label>
          <textarea
            id="feedback"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Provide any additional comments or suggestions..."
            rows={4}
          />
        </div>
        
        <button 
          type="submit" 
          className="submit-qa-btn" 
          disabled={loading || Object.values(ratings).some(r => r === 0)}
        >
          {loading ? 'Submitting...' : 'Submit Assessment'}
        </button>
      </form>
    </div>
  );
};

export default QualityAssurance;
