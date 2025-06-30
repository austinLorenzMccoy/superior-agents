import React from 'react';
import './LandingPage.css';
import LandingHeader from './LandingHeader';

interface LandingPageProps {
  onLoginClick: () => void;
}

const LandingPage: React.FC<LandingPageProps> = ({ onLoginClick }) => {
  return (
    <div className="landing-container">
      <LandingHeader onLoginClick={onLoginClick} />
      <section className="hero-section">
        <div className="hero-content">
          <h1>Welcome to GigNova</h1>
          <p className="hero-subtitle">
            The next generation AI-powered freelancing platform
          </p>
          <div className="hero-actions">
            <button className="primary-btn" onClick={onLoginClick}>
              Get Started
            </button>
            <a href="#features" className="secondary-btn">
              Learn More
            </a>
          </div>
        </div>
        <div className="hero-image">
          <img src="/hero-illustration.svg" alt="GigNova Platform" />
        </div>
      </section>

      <section id="features" className="features-section">
        <h2>Why Choose GigNova?</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">
              <i className="ai-icon"></i>
            </div>
            <h3>AI-Powered Matching</h3>
            <p>
              Our intelligent agents match you with the perfect freelancers for your project needs.
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">
              <i className="secure-icon"></i>
            </div>
            <h3>Secure Payments</h3>
            <p>
              Blockchain-based escrow system ensures secure and transparent transactions.
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">
              <i className="quality-icon"></i>
            </div>
            <h3>Quality Assurance</h3>
            <p>
              Automated quality checks ensure your project meets the highest standards.
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">
              <i className="smart-icon"></i>
            </div>
            <h3>Smart Contracts</h3>
            <p>
              Automated contract creation and management for seamless collaboration.
            </p>
          </div>
        </div>
      </section>

      <section className="how-it-works">
        <h2>How It Works</h2>
        <div className="workflow-steps">
          <div className="workflow-step">
            <div className="step-number">1</div>
            <h3>Post Your Job</h3>
            <p>Describe your project needs, budget, and timeline.</p>
          </div>
          
          <div className="workflow-step">
            <div className="step-number">2</div>
            <h3>Get Matched</h3>
            <p>Our AI agents find the perfect freelancers for your job.</p>
          </div>
          
          <div className="workflow-step">
            <div className="step-number">3</div>
            <h3>Collaborate</h3>
            <p>Work together with transparent communication and milestones.</p>
          </div>
          
          <div className="workflow-step">
            <div className="step-number">4</div>
            <h3>Quality Assurance</h3>
            <p>Automated checks ensure your project meets requirements.</p>
          </div>
          
          <div className="workflow-step">
            <div className="step-number">5</div>
            <h3>Payment</h3>
            <p>Secure payment release once work is approved.</p>
          </div>
        </div>
      </section>

      <section className="cta-section">
        <div className="cta-content">
          <h2>Ready to transform your freelancing experience?</h2>
          <p>Join GigNova today and experience the future of work.</p>
          <button className="primary-btn" onClick={onLoginClick}>
            Get Started Now
          </button>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;
