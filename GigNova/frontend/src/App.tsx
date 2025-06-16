import React, { useState, FormEvent, ChangeEvent } from 'react'
import './App.css'

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

// This type is used for freelancer profiles and will be used in future features
// @ts-ignore - Will be used in future features
interface FreelancerProfile {
  user_id: string;
  name: string;
  skills: string[];
  experience_years: number;
  hourly_rate: number;
  bio: string;
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [jobs, setJobs] = useState<JobPost[]>([]);
  const [activeTab, setActiveTab] = useState('jobs');
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [loginForm, setLoginForm] = useState({ username: '', password: '', role: 'client' });
  
  // API base URL
  const API_BASE_URL = 'http://localhost:8889/api/v1';

  // Handle login
  const handleLoginSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: loginForm.username,
          password: loginForm.password,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setUser({
          id: data.user_id,
          username: loginForm.username,
          role: data.role,
          token: data.access_token,
        });
        setIsLoginModalOpen(false);
        fetchJobs(data.access_token);
      } else {
        alert('Login failed. Please check your credentials.');
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('An error occurred during login.');
    }
  };

  // Handle register
  const handleRegisterSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: loginForm.username,
          password: loginForm.password,
          role: loginForm.role,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Registration successful! User ID: ${data.user_id}`);
        // Auto-login after registration
        handleLoginSubmit(e);
      } else {
        const errorData = await response.json();
        alert(`Registration failed: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Registration error:', error);
      alert('An error occurred during registration.');
    }
  };

  // Fetch jobs
  const fetchJobs = async (token: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/jobs`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setJobs(data);
      } else {
        console.error('Failed to fetch jobs');
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  // Logout handler
  const handleLogout = () => {
    setUser(null);
    setJobs([]);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="logo-container">
          <img src="/gignova-logo.svg" alt="GigNova Logo" className="app-logo" />
          <h1>GigNova</h1>
        </div>
        <div className="header-actions">
          {user ? (
            <>
              <span className="user-welcome">Welcome, {user.username} ({user.role})</span>
              <button className="logout-btn" onClick={handleLogout}>Logout</button>
            </>
          ) : (
            <button className="login-btn" onClick={() => setIsLoginModalOpen(true)}>Login / Register</button>
          )}
        </div>
      </header>

      <main className="app-main">
        {user ? (
          <>
            <nav className="app-nav">
              <ul>
                <li className={activeTab === 'jobs' ? 'active' : ''} onClick={() => setActiveTab('jobs')}>Jobs</li>
                <li className={activeTab === 'freelancers' ? 'active' : ''} onClick={() => setActiveTab('freelancers')}>Freelancers</li>
                <li className={activeTab === 'profile' ? 'active' : ''} onClick={() => setActiveTab('profile')}>My Profile</li>
              </ul>
            </nav>

            <div className="content-area">
              {activeTab === 'jobs' && (
                <div className="jobs-container">
                  <h2>Available Jobs</h2>
                  {jobs.length > 0 ? (
                    <div className="jobs-list">
                      {jobs.map((job: JobPost) => (
                        <div key={job.job_id} className="job-card">
                          <h3>{job.title}</h3>
                          <p className="job-status">Status: {job.status}</p>
                          <p className="job-budget">Budget: ${job.budget_min} - ${job.budget_max}</p>
                          <button className="view-job-btn">View Details</button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="no-jobs">No jobs available at the moment.</p>
                  )}
                </div>
              )}

              {activeTab === 'freelancers' && (
                <div className="freelancers-container">
                  <h2>Find Freelancers</h2>
                  <p>This feature is coming soon!</p>
                </div>
              )}

              {activeTab === 'profile' && (
                <div className="profile-container">
                  <h2>My Profile</h2>
                  <div className="profile-details">
                    <p><strong>Username:</strong> {user.username}</p>
                    <p><strong>Role:</strong> {user.role}</p>
                    <p><strong>User ID:</strong> {user.id}</p>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="welcome-container">
            <div className="logo-container">
              <img src="/gignova-logo.svg" alt="GigNova Logo" className="app-logo" />
              <h1>GigNova</h1>
            </div>
            <p>The Self-Evolving Talent Ecosystem powered by AI</p>
            <div className="feature-cards">
              <div className="feature-card">
                <h3>AI-Powered Matching</h3>
                <p>Intelligent matching of freelancers to jobs based on skills and experience</p>
              </div>
              <div className="feature-card">
                <h3>Smart Contracts</h3>
                <p>Secure blockchain-based escrow and payment system</p>
              </div>
              <div className="feature-card">
                <h3>Quality Assurance</h3>
                <p>AI-driven validation of deliverables against requirements</p>
              </div>
            </div>
            <button className="get-started-btn" onClick={() => setIsLoginModalOpen(true)}>Get Started</button>
          </div>
        )}
      </main>

      {isLoginModalOpen && (
        <div className="modal-overlay">
          <div className="login-modal">
            <button className="close-modal" onClick={() => setIsLoginModalOpen(false)}>×</button>
            <h2>Login / Register</h2>
            <form onSubmit={handleLoginSubmit} className="login-form">
              <div className="form-group">
                <label htmlFor="username">Username</label>
                <input 
                  type="text" 
                  id="username" 
                  value={loginForm.username} 
                  onChange={(e) => setLoginForm({...loginForm, username: e.target.value})}
                  required 
                />
              </div>
              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input 
                  type="password" 
                  id="password" 
                  value={loginForm.password} 
                  onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                  required 
                />
              </div>
              <div className="form-group">
                <label>I am a:</label>
                <div className="role-selector">
                  <label>
                    <input 
                      type="radio" 
                      name="role" 
                      value="client" 
                      checked={loginForm.role === 'client'} 
                      onChange={() => setLoginForm({...loginForm, role: 'client'})} 
                    />
                    Client
                  </label>
                  <label>
                    <input 
                      type="radio" 
                      name="role" 
                      value="freelancer" 
                      checked={loginForm.role === 'freelancer'} 
                      onChange={() => setLoginForm({...loginForm, role: 'freelancer'})} 
                    />
                    Freelancer
                  </label>
                </div>
              </div>
              <div className="form-actions">
                <button type="submit" className="login-submit">Login</button>
                <button type="button" className="register-btn" onClick={() => handleRegisterSubmit(new Event('submit') as unknown as FormEvent<HTMLFormElement>)}>Register</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <footer className="app-footer">
        <p>© {new Date().getFullYear()} GigNova - The Self-Evolving Talent Ecosystem</p>
      </footer>
    </div>
  )
}

export default App
