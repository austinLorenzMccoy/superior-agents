# GigNova Backend: Getting Started Guide for Beginners

Welcome to GigNova! This guide will help you understand how to use the GigNova backend system as a new developer. We'll walk through basic concepts, setup, and provide examples of common operations.

## What is GigNova?

GigNova is a decentralized freelancing platform powered by AI agents that facilitate job matching, negotiation, quality assurance, and payment processing. The platform connects clients with freelancers while using AI to optimize the entire workflow.

## Quick Setup

Before diving into examples, make sure you have:

1. Installed Python 3.8+
2. Set up your virtual environment
3. Installed dependencies with `pip install -e .`
4. Created a `.env` file with necessary environment variables

If you haven't done these steps, refer to the main README.md for detailed setup instructions.

## Core Concepts

GigNova's backend consists of several key components:

- **API Layer**: FastAPI endpoints that handle HTTP requests
- **Orchestrator**: Coordinates AI agents and manages job lifecycles
- **Agents**: Specialized AI components for different tasks
- **Storage**: Vector database and file storage systems
- **Blockchain**: Handles contracts and payments

## Example Usage Scenarios

Let's walk through some common scenarios to understand how the system works.

### Scenario 1: Creating a New Job Posting

As a client, you want to post a new job on the platform:

```python
import requests

# Authenticate and get token
auth_response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"username": "client_user", "password": "your_password"}
)
token = auth_response.json()["token"]

# Create a new job posting
job_data = {
    "title": "Build a React Landing Page",
    "description": "Need a responsive landing page built with React and styled-components",
    "skills": ["React", "CSS", "JavaScript"],
    "budget_min": 300,
    "budget_max": 500,
    "deadline": "2025-07-30"
}

response = requests.post(
    "http://localhost:8000/api/jobs/create",
    json=job_data,
    headers={"Authorization": f"Bearer {token}"}
)

print(f"Job created with ID: {response.json()['job_id']}")
```

### Scenario 2: Finding Matching Freelancers

The system automatically matches your job with suitable freelancers:

```python
# Get matches for your job
job_id = "job_12345"  # Use the ID from the previous response
matches_response = requests.get(
    f"http://localhost:8000/api/jobs/{job_id}/matches",
    headers={"Authorization": f"Bearer {token}"}
)

matches = matches_response.json()["matches"]
for match in matches:
    print(f"Freelancer: {match['username']} - Match score: {match['score']}")
```

### Scenario 3: Accepting a Proposal

When a freelancer sends a proposal, you can accept it:

```python
proposal_id = "proposal_789"  # ID of the proposal you want to accept
response = requests.post(
    f"http://localhost:8000/api/proposals/{proposal_id}/accept",
    headers={"Authorization": f"Bearer {token}"}
)

print(f"Proposal accepted, contract status: {response.json()['contract_status']}")
```

### Scenario 4: Submitting Deliverables (as a Freelancer)

As a freelancer, you can submit your work:

```python
# First authenticate as the freelancer
freelancer_token = "..."  # Get this by authenticating as the freelancer

# Submit deliverables
contract_id = "contract_456"
deliverable_data = {
    "description": "Completed landing page with all requested features",
    "files": ["main.js", "styles.css", "index.html"],
    "notes": "Implemented all requirements plus added animations"
}

response = requests.post(
    f"http://localhost:8000/api/contracts/{contract_id}/submit",
    json=deliverable_data,
    headers={"Authorization": f"Bearer {freelancer_token}"}
)

print(f"Submission status: {response.json()['status']}")
```

### Scenario 5: Using the Python SDK

For easier integration, you can use our Python SDK:

```python
from gignova.client import GigNovaClient

# Initialize client
client = GigNovaClient(api_key="your_api_key")

# Create a job
job = client.create_job(
    title="Data Analysis Project",
    description="Need help analyzing customer survey data",
    skills=["Python", "Pandas", "Data Visualization"],
    budget_min=200,
    budget_max=400
)

# Get job status
status = client.get_job_status(job.id)
print(f"Job status: {status}")
```

## Working with AI Agents

GigNova's AI agents can be accessed directly for testing or custom integrations:

```python
from gignova.agents import MatchingAgent, NegotiationAgent

# Initialize the matching agent
matching_agent = MatchingAgent()

# Find matches for a job
job_description = "Need a Python developer with experience in FastAPI"
matches = matching_agent.find_matches(job_description)

# Use negotiation agent to suggest a fair price
negotiation_agent = NegotiationAgent()
suggested_price = negotiation_agent.suggest_price(
    job_description=job_description,
    freelancer_experience="5 years",
    market_rates=[300, 350, 400]  # Similar job rates
)

print(f"Suggested price range: ${suggested_price['min']} - ${suggested_price['max']}")
```

## Local Blockchain Operations

GigNova uses a simplified blockchain implementation for contracts and payments:

```python
from gignova.blockchain.manager import BlockchainManager

# Initialize blockchain manager
blockchain = BlockchainManager()

# Create a smart contract
contract = blockchain.create_contract(
    client_id="client_123",
    freelancer_id="freelancer_456",
    job_id="job_789",
    payment_amount=350,
    deadline="2025-07-30"
)

# Execute payment when job is complete
transaction = blockchain.execute_payment(
    contract_id=contract.id,
    amount=350,
    from_address="client_123",
    to_address="freelancer_456"
)

print(f"Payment completed: {transaction.id}")
```

## Testing the API Directly

You can also test the API endpoints directly using the built-in Swagger UI:

1. Start the server: `python -m gignova.main`
2. Open your browser and navigate to: `http://localhost:8000/docs`
3. Use the interactive interface to test different endpoints

## Debugging Tips

If you encounter issues:

1. Check the logs in `logs/gignova.log`
2. Verify your `.env` configuration
3. Make sure the server is running (`python -m gignova.main`)
4. Check database connections with `python -m gignova.tools.db_check`

## Next Steps

Once you're comfortable with these basics, you can:

1. Explore the agent configuration options in `gignova/config/`
2. Customize the matching algorithm in `gignova/agents/matching.py`
3. Extend the API with new endpoints in `gignova/api/`
4. Implement your own specialized agents

## Need Help?

- Check the full API documentation in the `docs/api/` directory
- Review code examples in the `examples/` folder
- Join our developer community on Discord

Happy coding with GigNova!
