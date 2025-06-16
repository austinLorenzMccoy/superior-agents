#!/usr/bin/env python3
"""
GigNova Basic Workflow Example

This script demonstrates a complete workflow using the GigNova backend:
1. User registration and authentication
2. Creating a job posting
3. Finding matching freelancers
4. Accepting a proposal
5. Submitting and reviewing deliverables
6. Completing payment

Run this script to see a simulated workflow in action.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta

# Add the project root to the path so we can import the gignova package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import directly from the package for better IDE support
try:
    from gignova.client import GigNovaClient
    from gignova.blockchain.manager import BlockchainManager
except ImportError:
    print("Could not import GigNova modules directly. Using API calls instead.")
    GigNovaClient = None
    BlockchainManager = None

# Configuration
API_BASE_URL = "http://localhost:8000/api"
USE_SDK = GigNovaClient is not None

def print_step(step_number, description):
    """Print a formatted step header"""
    print("\n" + "="*80)
    print(f"STEP {step_number}: {description}")
    print("="*80)

def print_response(response_data):
    """Pretty print API response data"""
    print("\nResponse:")
    print(json.dumps(response_data, indent=2))
    print("-"*40)

def register_user(username, password, role):
    """Register a new user"""
    response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "username": username,
            "password": password,
            "email": f"{username}@example.com",
            "role": role
        }
    )
    return response.json()

def login_user(username, password):
    """Login and get authentication token"""
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "username": username,
            "password": password
        }
    )
    return response.json()

def create_job(token, job_data):
    """Create a new job posting"""
    response = requests.post(
        f"{API_BASE_URL}/jobs/create",
        json=job_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

def get_job_matches(token, job_id):
    """Get freelancer matches for a job"""
    response = requests.get(
        f"{API_BASE_URL}/jobs/{job_id}/matches",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

def create_proposal(token, job_id, proposal_data):
    """Submit a proposal for a job"""
    response = requests.post(
        f"{API_BASE_URL}/jobs/{job_id}/proposals",
        json=proposal_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

def accept_proposal(token, proposal_id):
    """Accept a proposal"""
    response = requests.post(
        f"{API_BASE_URL}/proposals/{proposal_id}/accept",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

def submit_deliverable(token, contract_id, deliverable_data):
    """Submit deliverables for a contract"""
    response = requests.post(
        f"{API_BASE_URL}/contracts/{contract_id}/submit",
        json=deliverable_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

def approve_deliverable(token, contract_id):
    """Approve deliverables and release payment"""
    response = requests.post(
        f"{API_BASE_URL}/contracts/{contract_id}/approve",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

def run_sdk_example():
    """Run the example workflow using the SDK"""
    client = GigNovaClient()
    
    # Register users
    print_step(1, "Registering users")
    client_user = client.register_user(
        username="example_client",
        password="securepass123",
        email="client@example.com",
        role="client"
    )
    print(f"Registered client: {client_user.username}")
    
    freelancer_user = client.register_user(
        username="example_freelancer",
        password="securepass456",
        email="freelancer@example.com",
        role="freelancer"
    )
    print(f"Registered freelancer: {freelancer_user.username}")
    
    # Create freelancer profile
    print_step(2, "Creating freelancer profile")
    profile = client.create_freelancer_profile(
        user_id=freelancer_user.id,
        name="Alex Developer",
        skills=["Python", "FastAPI", "React"],
        experience_years=5,
        hourly_rate=45,
        bio="Experienced full-stack developer specializing in Python and React"
    )
    print(f"Created profile for: {profile.name}")
    
    # Create a job
    print_step(3, "Creating a job posting")
    deadline = datetime.now() + timedelta(days=14)
    job = client.create_job(
        title="Build a RESTful API",
        description="Need a RESTful API built with FastAPI for a new mobile app",
        skills=["Python", "FastAPI", "API Design"],
        budget_min=500,
        budget_max=1000,
        deadline=deadline.isoformat()
    )
    print(f"Created job: {job.title} (ID: {job.id})")
    
    # Get matches
    print_step(4, "Finding freelancer matches")
    matches = client.get_job_matches(job.id)
    print(f"Found {len(matches)} potential freelancers")
    for match in matches:
        print(f"- {match.freelancer_name}: {match.match_score}% match")
    
    # Create proposal
    print_step(5, "Submitting a proposal")
    proposal = client.create_proposal(
        job_id=job.id,
        freelancer_id=freelancer_user.id,
        price=750,
        delivery_time=10,  # days
        cover_letter="I'm very interested in this project and have extensive experience with FastAPI."
    )
    print(f"Submitted proposal (ID: {proposal.id})")
    
    # Accept proposal
    print_step(6, "Accepting the proposal")
    contract = client.accept_proposal(proposal.id)
    print(f"Created contract (ID: {contract.id})")
    
    # Submit deliverables
    print_step(7, "Submitting deliverables")
    submission = client.submit_deliverable(
        contract_id=contract.id,
        description="Completed API with documentation",
        files=["api.py", "docs.md"],
        notes="All endpoints implemented and tested"
    )
    print(f"Submitted deliverables (Status: {submission.status})")
    
    # Approve and pay
    print_step(8, "Approving work and releasing payment")
    payment = client.approve_deliverable(contract.id)
    print(f"Payment completed (Transaction ID: {payment.transaction_id})")
    
    print("\nWorkflow completed successfully!")

def run_api_example():
    """Run the example workflow using direct API calls"""
    # Register users
    print_step(1, "Registering users")
    client_data = register_user("example_client", "securepass123", "client")
    print_response(client_data)
    
    freelancer_data = register_user("example_freelancer", "securepass456", "freelancer")
    print_response(freelancer_data)
    
    # Login
    print_step(2, "Logging in")
    client_auth = login_user("example_client", "securepass123")
    client_token = client_auth.get("token")
    print(f"Client token: {client_token[:10]}...")
    
    freelancer_auth = login_user("example_freelancer", "securepass456")
    freelancer_token = freelancer_auth.get("token")
    print(f"Freelancer token: {freelancer_token[:10]}...")
    
    # Create a job
    print_step(3, "Creating a job posting")
    deadline = (datetime.now() + timedelta(days=14)).isoformat()
    job_data = {
        "title": "Build a RESTful API",
        "description": "Need a RESTful API built with FastAPI for a new mobile app",
        "skills": ["Python", "FastAPI", "API Design"],
        "budget_min": 500,
        "budget_max": 1000,
        "deadline": deadline
    }
    job_response = create_job(client_token, job_data)
    job_id = job_response.get("job_id")
    print_response(job_response)
    
    # Get matches
    print_step(4, "Finding freelancer matches")
    matches_response = get_job_matches(client_token, job_id)
    print_response(matches_response)
    
    # Create proposal
    print_step(5, "Submitting a proposal")
    proposal_data = {
        "price": 750,
        "delivery_time": 10,  # days
        "cover_letter": "I'm very interested in this project and have extensive experience with FastAPI."
    }
    proposal_response = create_proposal(freelancer_token, job_id, proposal_data)
    proposal_id = proposal_response.get("proposal_id")
    print_response(proposal_response)
    
    # Accept proposal
    print_step(6, "Accepting the proposal")
    contract_response = accept_proposal(client_token, proposal_id)
    contract_id = contract_response.get("contract_id")
    print_response(contract_response)
    
    # Submit deliverables
    print_step(7, "Submitting deliverables")
    deliverable_data = {
        "description": "Completed API with documentation",
        "files": ["api.py", "docs.md"],
        "notes": "All endpoints implemented and tested"
    }
    submission_response = submit_deliverable(freelancer_token, contract_id, deliverable_data)
    print_response(submission_response)
    
    # Approve and pay
    print_step(8, "Approving work and releasing payment")
    payment_response = approve_deliverable(client_token, contract_id)
    print_response(payment_response)
    
    print("\nWorkflow completed successfully!")

def main():
    """Main function to run the example"""
    print("GigNova Basic Workflow Example")
    print("------------------------------")
    
    if USE_SDK:
        print("Using GigNova SDK")
        run_sdk_example()
    else:
        print("Using direct API calls")
        run_api_example()

if __name__ == "__main__":
    main()
