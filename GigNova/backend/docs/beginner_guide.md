# GigNova Backend: Visual Guide for Beginners

This guide provides a visual overview of the GigNova backend architecture and workflow to help new developers understand how the system works.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           GigNova Backend                               │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────────┤
│             │             │             │             │                 │
│  FastAPI    │             │  AI Agents  │  Storage    │  Blockchain     │
│  Endpoints  │ Orchestrator│             │  Layer      │  Layer          │
│             │             │             │             │                 │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────────┤
│ /auth       │             │ Matching    │ Vector DB   │ Contracts       │
│ /users      │ Job         │ Agent       │ (In-memory) │                 │
│ /jobs       │ Lifecycle   │             │             │ Payments        │
│ /proposals  │ Management  │ Negotiation │ File        │                 │
│ /contracts  │             │ Agent       │ Storage     │ Transaction     │
│ /payments   │ Agent       │             │ (Local)     │ History         │
│             │ Coordination│ QA Agent    │             │                 │
│             │             │             │             │                 │
│             │ Event       │ Payment     │             │                 │
│             │ Processing  │ Agent       │             │                 │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────────┘
```

## Job Lifecycle Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Posted  │────▶│ Matching │────▶│Negotiation│────▶│   Work   │────▶│ Payment  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                │                │                │
     ▼                ▼                ▼                ▼                ▼
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│Client    │     │AI finds  │     │Proposal  │     │Freelancer│     │QA Agent  │
│creates   │     │suitable  │     │submitted │     │submits   │     │validates │
│job       │     │freelancers│     │& accepted│     │work      │     │work      │
└──────────┘     └──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                                         │
                                                                         ▼
                                                                    ┌──────────┐
                                                                    │Payment   │
                                                                    │released  │
                                                                    └──────────┘
```

## API Endpoints Overview

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/api/auth/register` | POST | Register new user | `{"username": "user1", "password": "pass", "role": "client"}` |
| `/api/auth/login` | POST | Authenticate user | `{"username": "user1", "password": "pass"}` |
| `/api/jobs/create` | POST | Create new job | `{"title": "Web Dev", "budget_min": 500, ...}` |
| `/api/jobs/{job_id}/matches` | GET | Get freelancer matches | Returns list of matching freelancers |
| `/api/jobs/{job_id}/proposals` | POST | Submit proposal | `{"price": 750, "delivery_time": 10, ...}` |
| `/api/proposals/{proposal_id}/accept` | POST | Accept proposal | Creates a contract |
| `/api/contracts/{contract_id}/submit` | POST | Submit deliverables | `{"description": "Completed work", ...}` |
| `/api/contracts/{contract_id}/approve` | POST | Approve work | Releases payment |

## Data Models

### User

```json
{
  "id": "user_12345",
  "username": "johndoe",
  "email": "john@example.com",
  "role": "client",
  "created_at": "2025-06-16T12:00:00Z"
}
```

### Job

```json
{
  "job_id": "job_67890",
  "title": "Build a React Landing Page",
  "description": "Need a responsive landing page...",
  "skills": ["React", "CSS", "JavaScript"],
  "budget_min": 300,
  "budget_max": 500,
  "deadline": "2025-07-30",
  "status": "posted",
  "client_id": "user_12345"
}
```

### Proposal

```json
{
  "proposal_id": "prop_24680",
  "job_id": "job_67890",
  "freelancer_id": "user_54321",
  "price": 400,
  "delivery_time": 7,
  "cover_letter": "I'm interested in this project...",
  "status": "pending",
  "created_at": "2025-06-17T09:30:00Z"
}
```

### Contract

```json
{
  "contract_id": "contract_13579",
  "job_id": "job_67890",
  "client_id": "user_12345",
  "freelancer_id": "user_54321",
  "price": 400,
  "deadline": "2025-07-15",
  "status": "in_progress",
  "created_at": "2025-06-18T10:00:00Z"
}
```

## Blockchain Simplified

GigNova uses a simplified blockchain implementation for contracts and payments:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Contract    │────▶│  Escrow      │────▶│  Payment     │
│  Creation    │     │  Holding     │     │  Release     │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│Contract terms│     │Client funds  │     │Funds transfer│
│recorded in   │     │locked in     │     │to freelancer │
│blockchain    │     │smart contract│     │wallet        │
└──────────────┘     └──────────────┘     └──────────────┘
```

## AI Agent Interactions

```
                         ┌─────────────────┐
                         │   Orchestrator  │
                         └────────┬────────┘
                                  │
                                  │ coordinates
                                  │
          ┌─────────────┬─────────┴────────┬─────────────┐
          │             │                  │             │
          ▼             ▼                  ▼             ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Matching Agent  │ │Negotiation   │ │ QA Agent     │ │ Payment      │
│                 │ │Agent         │ │              │ │ Agent        │
└─────────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
  │                   │                │                │
  │ finds matches     │ helps with     │ validates      │ handles
  │                   │ pricing        │ deliverables   │ transactions
  ▼                   ▼                ▼                ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Freelancer      │ │ Fair Price   │ │ Quality      │ │ Secure       │
│ Recommendations │ │ Determination│ │ Assessment   │ │ Payments     │
└─────────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

## Getting Started Steps

1. **Setup Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

2. **Start the Server**
   ```bash
   python -m gignova.main
   ```

3. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - API Endpoints: http://localhost:8000/api/...

4. **Run Example Workflow**
   ```bash
   python examples/basic_workflow.py
   ```

## Common Development Tasks

- **Add a new API endpoint**:
  Edit `gignova/api/routes/` files

- **Modify agent behavior**:
  Edit files in `gignova/agents/`

- **Change blockchain behavior**:
  Edit `gignova/blockchain/manager.py`

- **Update database models**:
  Edit `gignova/models/`

## Need More Help?

Refer to the detailed documentation in:
- `docs/getting_started.md` - Comprehensive guide for beginners
- `examples/` directory - Example code for common operations
- `README.md` - Main project documentation
