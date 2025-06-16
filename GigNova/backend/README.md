# GigNova Backend

GigNova is a decentralized freelancing platform that uses AI agents to facilitate job matching, negotiation, quality assurance, and payment processing.

## Architecture

The backend is modularized into several components:

- **API Routes**: FastAPI endpoints for user interaction
- **Orchestrator**: Coordinates the different agents and manages job lifecycle
- **Agents**: Specialized AI agents for matching, negotiation, QA, and payment
- **Database**: Simple in-memory vector storage for semantic search and agent learning
- **Blockchain**: Simple local implementation for managing contracts and payments
- **File Storage**: Local filesystem for storing job deliverables and other content

## Implementation

This version uses simplified implementations that don't require external services:

- **Vector Storage**: Simple in-memory implementation with numpy for vector operations
- **File Storage**: Local filesystem implementation with content-addressable storage
- **Blockchain**: Local JSON-based implementation that simulates contracts and transactions

These implementations completely replace the need for external services like Qdrant, IPFS, and blockchain nodes, making it much easier to run the application.

## Setup Instructions

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -e .
   ```

### Environment Variables

Create a `.env` file in the backend directory with the following variables:

```
DEV_MODE=true
JWT_SECRET=your_jwt_secret_here
```

Note: No OpenAI API key is required since we're using local implementations for all services.

## Testing Local Implementations

A test script is provided to verify that the local implementations of external services are working correctly:

```bash
python test_local_implementations.py
```

This script tests:

1. **VectorManager**: Storing job and freelancer embeddings, and finding matching freelancers using semantic search
2. **IPFSManager**: Storing and retrieving files and JSON data using local file storage
3. **BlockchainManager**: Creating job contracts, checking status, completing jobs, and releasing payments

### API Testing

To test the API endpoints:

1. Start the server:
   ```bash
   PORT=8889 python -m gignova.app
   ```

2. Test the health endpoint:
   ```bash
   curl -X GET http://localhost:8889/health
   ```

3. Register a user:
   ```bash
   curl -X POST http://localhost:8889/api/v1/auth/register -H "Content-Type: application/json" -d '{"username": "testuser", "password": "password123", "role": "client"}'
   ```

4. Login to get a JWT token:
   ```bash
   curl -X POST http://localhost:8889/api/v1/auth/login -H "Content-Type: application/json" -d '{"username": "testuser", "password": "password123"}'
   ```

5. Create a job post (replace TOKEN with your JWT token):
   ```bash
   curl -X POST http://localhost:8889/api/v1/jobs -H "Content-Type: application/json" -H "Authorization: Bearer TOKEN" -d '{"title": "Test Job", "description": "This is a test job", "skills": ["python", "fastapi"], "budget_min": 400, "budget_max": 600, "deadline": "2025-07-16T00:00:00Z", "client_id": "YOUR_USER_ID", "requirements": ["Must have experience with API testing"]}'
   ```
## API Configuration

For local development with our in-memory implementations, you only need these settings:

```
# Required settings
JWT_SECRET=your_jwt_secret_key
DEV_MODE=true
ENVIRONMENT=dev

# Server configuration
PORT=8889  # Optional, defaults to 8888
```

### External Services Configuration (Not needed for local development)

These settings are only needed if you want to use external services instead of local implementations:

```
# External services (not needed when DEV_MODE=true)
# OPENAI_API_KEY=your_openai_api_key
# QDRANT_URL=http://localhost:6333
# IPFS_API_URL=/ip4/127.0.0.1/tcp/5001
# WEB3_PROVIDER_URI=http://localhost:8545
# WALLET_PRIVATE_KEY=your_private_key
```

The `DEV_MODE=true` setting enables the local implementations for vector database, file storage, and blockchain.

### Running the Application

Start the application with:

```bash
python -m gignova.app
```

The API will be available at http://localhost:8000

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development Notes

- Local storage for files is in `~/.gignova/storage/`
- Local blockchain data is in `~/.gignova/blockchain/`
- The application uses in-memory storage for vector embeddings
- No external services are required to run the application in development mode

## Testing

Run tests with:

```bash
pytest
```

## License

[MIT License](LICENSE)
