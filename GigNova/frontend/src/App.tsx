import React, { useState, useEffect } from 'react';
import './App.css';
import LoginModal from './components/auth/LoginModal';
import { fetchJobs } from './utils/apiConfig';
import { Job } from './utils/api';
import QualityAssurance from './components/qa/QualityAssurance';
import PaymentSystem from './components/payment/PaymentSystem';
import { getStoredAuthData, storeAuthData, clearAuthData } from './utils/auth';
import LoadingSpinner from './components/common/LoadingSpinner';
import LandingPage from './components/common/LandingPage';
import JobRecommendations from './components/jobs/JobRecommendations';
import Footer from './components/common/Footer';

// Define types for our application
interface User {
  id: string;
  username: string;
  role: 'client' | 'freelancer';
  token?: string;
}

interface JobPost {
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

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [jobs, setJobs] = useState<JobPost[]>([]);
  const [activeTab, setActiveTab] = useState<'jobs' | 'profile' | 'qa' | 'payment' | 'recommendations'>('jobs');
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedJobForQA, setSelectedJobForQA] = useState<string>('');
  const [showQAAssessment, setShowQAAssessment] = useState<boolean>(false);

  // API base URL
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8889/api/v1';

  // Check for stored authentication data on component mount
  useEffect(() => {
    const storedAuth = getStoredAuthData();
    
    if (storedAuth) {
      setUser({
        id: storedAuth.userId,
        username: storedAuth.username,
        role: storedAuth.role,
        token: storedAuth.token
      });
      
      loadJobs(storedAuth.token);
    }
    
    setIsLoading(false);
  }, []);

  // Handle successful authentication
  const handleAuthSuccess = (token: string, userId: string, username: string, role: string) => {
    // Store auth data for persistent login
    storeAuthData(token, userId, username, role);
    
    // Set user object for dashboard display
    setUser({
      id: userId,
      username: username,
      role: role as 'client' | 'freelancer'
    });
    
    setIsLoginModalOpen(false);
    console.log('Authentication successful! Fetching real data from backend.');
    
    // Load real jobs from backend
    loadJobs(token);
  };

  // Fetch jobs using our API utility with fallback to mock data
  const loadJobs = async (token: string) => {
    try {
      // Use our configured API utility
      const { data, error } = await fetchJobs(token);
      
      if (error) {
        console.warn('Failed to fetch real jobs, using mock data:', error);
        // Use mock data as fallback
        loadMockJobs();
        return;
      }
      
      if (data) {
        setJobs(data);
      } else {
        // If no data returned, use mock data
        loadMockJobs();
      }
    } catch (error) {
      console.warn('Error loading jobs, using mock data:', error);
      // Use mock data as fallback
      loadMockJobs();
    }
  };
  
  // Load mock job data
  const loadMockJobs = () => {
    console.log('Loading mock job data');
    setJobs([
      {
        job_id: "job-1",
        title: "Website Development",
        description: "Create a responsive website for a small business",
        skills: ["React", "Node.js", "MongoDB", "AWS", "TypeScript"],
        budget_min: 1500,
        budget_max: 3000,
        deadline: '2025-07-30',
        status: 'posted',
        client_id: 'client-123'
      },
      {
        job_id: "job-2",
        title: "Mobile App Design",
        description: "Design UI/UX for a fitness tracking app",
        skills: ["Figma", "UI/UX", "Swift", "Kotlin", "Adobe XD"],
        budget_min: 2000,
        budget_max: 4500,
        deadline: '2025-08-15',
        status: 'posted',
        client_id: 'client-456'
      },
      {
        job_id: "job-3",
        title: "Smart Contract Development",
        description: "Develop Ethereum smart contracts for an NFT marketplace",
        skills: ["Solidity", "Blockchain", "Ethereum"],
        budget_min: 1200,
        budget_max: 2500,
        deadline: '2025-08-01',
        status: 'posted',
        client_id: 'client-789'
      },
      {
        job_id: "job-4",
        title: "E-commerce Platform Development",
        description: "Build a custom e-commerce platform with payment integration",
        skills: ["Shopify", "WooCommerce", "PHP", "JavaScript", "Payment Integration"],
        budget_min: 5000,
        budget_max: 12000,
        deadline: '2025-09-30',
        status: 'posted',
        client_id: 'client-234'
      },
      {
        job_id: "job-5",
        title: "Content Writing for Tech Blog",
        description: "Create technical articles for a software development blog",
        skills: ["Technical Writing", "SEO", "Research", "Editing"],
        budget_min: 500,
        budget_max: 1200,
        deadline: '2025-07-20',
        status: 'posted',
        client_id: 'client-567'
      },
      {
        job_id: "job-6",
        title: "AI Model Training",
        description: "Train and optimize machine learning models for image recognition",
        skills: ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Data Science"],
        budget_min: 3000,
        budget_max: 8000,
        deadline: '2025-08-25',
        status: 'posted',
        client_id: 'client-890'
      }
    ]);
  };

  // Logout handler
  const handleLogout = () => {
    clearAuthData();
    setUser(null);
    setJobs([]);
  };

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="app-loading">
        <div className="loading-content">
          <img src="/gignova-logo.svg" alt="GigNova Logo" className="app-logo" />
          <h2>Loading GigNova...</h2>
          <div className="loading-spinner-container">
            <LoadingSpinner size="large" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      {user ? (
        <>
          <header className="app-header">
            <div className="logo-container">
              <img src="/gignova-logo.svg" alt="GigNova Logo" className="app-logo" />
              <h1>GigNova</h1>
            </div>
            <div className="header-actions">
              <span className="user-welcome">Welcome, {user.username} ({user.role})</span>
              <button className="logout-btn" onClick={handleLogout}>Logout</button>
            </div>
          </header>

          <main className="app-main">
            <div className="dashboard-tabs">
              <button 
                className={`tab-button ${activeTab === 'jobs' ? 'active' : ''}`}
                onClick={() => setActiveTab('jobs')}
              >
                Jobs
              </button>
              {user?.role === 'freelancer' && (
                <button 
                  className={`tab-button ${activeTab === 'recommendations' ? 'active' : ''}`}
                  onClick={() => setActiveTab('recommendations')}
                >
                  Recommendations
                </button>
              )}
              <button 
                className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
                onClick={() => setActiveTab('profile')}
              >
                Profile
              </button>
              <button 
                className={`tab-button ${activeTab === 'qa' ? 'active' : ''}`}
                onClick={() => setActiveTab('qa')}
              >
                Quality Assurance
              </button>
              <button 
                className={`tab-button ${activeTab === 'payment' ? 'active' : ''}`}
                onClick={() => setActiveTab('payment')}
              >
                Payments
              </button>
            </div>

            <div className="dashboard-content">
              {activeTab === 'jobs' && (
                <div className="jobs-list">
                  <h2>Available Jobs</h2>
                  {jobs.length > 0 ? (
                    <ul>
                      {jobs.map(job => (
                        <li key={job.job_id} className="job-card">
                          <h3>{job.title}</h3>
                          <p>{job.description}</p>
                          <div className="job-details">
                            <span className="job-budget">${job.budget_min} - ${job.budget_max}</span>
                            <span className="job-deadline">Due: {job.deadline}</span>
                          </div>
                          <div className="job-skills">
                            {job.skills.map(skill => (
                              <span key={skill} className="skill-tag">{skill}</span>
                            ))}
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No jobs available at the moment.</p>
                  )}
                </div>
              )}
              
              {activeTab === 'recommendations' && user?.role === 'freelancer' && (
                <div className="recommendations-section">
                  <JobRecommendations 
                    userId={user.id}
                    token={user.token || ''}
                    apiBaseUrl={API_BASE_URL}
                  />
                </div>
              )}
              
              {activeTab === 'profile' && (
                <div className="profile-section">
                  <h2>Your Profile</h2>
                  <div className="profile-info">
                    <p><strong>Username:</strong> {user?.username}</p>
                    <p><strong>Role:</strong> {user?.role}</p>
                    <p><strong>User ID:</strong> {user?.id}</p>
                  </div>
                </div>
              )}
              
              {activeTab === 'qa' && (
                <div className="qa-section">
                  <h2>Quality Assurance</h2>
                  {jobs.length > 0 ? (
                    <div>
                      <p className="section-description">
                        Evaluate the quality of delivered work for your active jobs.
                      </p>
                      
                      {/* Job selection dropdown */}
                      <div className="qa-job-selection">
                        <h3>Select a job for quality assessment:</h3>
                        
                        <div className="qa-job-dropdown-container">
                          <select 
                            className="qa-job-dropdown"
                            onChange={(e) => setSelectedJobForQA(e.target.value)}
                            value={selectedJobForQA || ""}
                          >
                            <option value="" disabled>Choose a job...</option>
                            {jobs.map(job => (
                              <option key={job.job_id} value={job.job_id}>
                                {job.title} - Budget: ${job.budget_min}-${job.budget_max}
                              </option>
                            ))}
                          </select>
                          
                          <button 
                            className="qa-select-btn dropdown-btn"
                            onClick={() => setShowQAAssessment(true)}
                            disabled={!selectedJobForQA}
                          >
                            Start Assessment
                          </button>
                        </div>
                        
                        <h4 className="recent-jobs-heading">Recent Jobs:</h4>
                        <div className="qa-jobs-list">
                          {jobs.slice(0, 3).map(job => (
                            <div key={job.job_id} className="qa-job-card">
                              <div className="qa-job-info">
                                <h4>{job.title}</h4>
                                <p className="qa-job-skills">
                                  {job.skills.slice(0, 2).join(', ')}
                                  {job.skills.length > 2 ? '...' : ''}
                                </p>
                              </div>
                              <button 
                                className="qa-select-btn"
                                onClick={() => {
                                  setSelectedJobForQA(job.job_id);
                                  setShowQAAssessment(true);
                                }}
                              >
                                Start Assessment
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* QA component with selected job */}
                      {showQAAssessment && selectedJobForQA && (
                        <div className="qa-assessment">
                          <div className="qa-assessment-header">
                            <h3>Quality Assessment</h3>
                            <button 
                              className="close-assessment-btn"
                              onClick={() => setShowQAAssessment(false)}
                            >
                              ×
                            </button>
                          </div>
                          <div className="qa-component-wrapper">
                            <QualityAssurance jobId={selectedJobForQA} />
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p>No jobs available for quality assessment.</p>
                  )}
                </div>
              )}
              
              {activeTab === 'payment' && (
                <div className="payment-section">
                  <h2>Payment Management</h2>
                  <p className="section-description">
                    Securely manage payments for your jobs using traditional or blockchain methods.
                  </p>
                  
                  <div className="payment-options">
                    <h3>Payment Options</h3>
                    <div className="payment-cards">
                      <div className="payment-option-card">
                        <h4>Make a Payment</h4>
                        <p>Pay for completed work or fund an escrow contract</p>
                        <button 
                          className="payment-action-btn"
                          onClick={() => console.log('Initiate new payment')}
                        >
                          New Payment
                        </button>
                      </div>
                      
                      <div className="payment-option-card">
                        <h4>View Contracts</h4>
                        <p>Manage your active contracts and payment terms</p>
                        <button 
                          className="payment-action-btn secondary"
                          onClick={() => console.log('View contracts')}
                        >
                          View Contracts
                        </button>
                      </div>
                      
                      <div className="payment-option-card">
                        <h4>Payment History</h4>
                        <p>View your transaction history and payment status</p>
                        <button 
                          className="payment-action-btn secondary"
                          onClick={() => console.log('View payment history')}
                        >
                          View History
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  {/* Sample Payment component */}
                  <div className="payment-demo">
                    <h3>Demo Payment</h3>
                    <div className="payment-component-wrapper">
                      <PaymentSystem 
                        jobId="sample-job-123" 
                        amount={750} 
                        recipientId="freelancer-456"
                        onComplete={(txId) => console.log(`Payment completed with transaction ID: ${txId}`)}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </main>
        </>
      ) : (
        <LandingPage onLoginClick={() => setIsLoginModalOpen(true)} />
      )}

      {isLoginModalOpen && (
        <LoginModal 
          isOpen={isLoginModalOpen}
          onClose={() => setIsLoginModalOpen(false)}
          onLogin={handleAuthSuccess}
          apiBaseUrl={API_BASE_URL}
        />
      )}
      <Footer />
    </div>
  );
}

export default App;
