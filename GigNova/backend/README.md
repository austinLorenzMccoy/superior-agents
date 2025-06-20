# GigNova Backend

GigNova is a decentralized freelancing platform that uses AI agents to facilitate job matching, negotiation, quality assurance, and payment processing.

## Architecture

The backend is modularized into several components:

- **API Routes**: FastAPI endpoints for user interaction
- **Orchestrator**: Coordinates the different agents and manages job lifecycle
- **Agents**: Specialized AI agents for matching, negotiation, QA, and payment
- **MCP Integration**: Model Context Protocol servers for vector storage, blockchain, file storage, analytics, and social media
- **Database**: Vector storage for semantic search and agent learning
- **Blockchain**: Smart contract management for escrow and payments
- **File Storage**: Content-addressable storage for job deliverables and other content

## Implementation

GigNova is fully integrated with MCP (Model Context Protocol) servers and supports two modes of operation controlled by the `DEV_MODE` environment variable:

### Development Mode (`DEV_MODE=true`)

Uses simplified local implementations for easier development and testing:

- **Vector Storage**: Simple in-memory implementation with numpy for vector operations
- **File Storage**: Local filesystem implementation with content-addressable storage
- **Blockchain**: Local JSON-based implementation that simulates contracts and transactions

### Production Mode (`DEV_MODE=false` or not set)

Uses MCP servers for production-grade services with enhanced scalability, interoperability, and asynchronous operation:

- **Vector Storage**: MCP vector server for embedding storage and semantic search
- **File Storage**: MCP storage server for content-addressable file storage
- **Blockchain**: MCP blockchain server for contract deployment and payment processing
- **Analytics**: MCP analytics server for event logging and metrics collection
- **Social Media**: MCP social media server for automated posting and engagement
- **LLM Integration**: Groq LLM models for advanced text generation and structured outputs

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

#### Required Environment Variables

```
JWT_SECRET=your_jwt_secret_here  # Secret for JWT token generation and validation

# LLM API Keys
GROQ_API_KEY=your_groq_api_key_here  # API key for Groq LLM integration
```

#### MCP Server Configuration (Production Mode)

By default, the system operates in production mode using MCP servers. Configure your MCP server endpoints:

```
# MCP Server URLs
VECTOR_MCP_SERVER=https://your-vector-mcp-server.com
BLOCKCHAIN_MCP_SERVER=https://your-blockchain-mcp-server.com
STORAGE_MCP_SERVER=https://your-storage-mcp-server.com
ANALYTICS_MCP_SERVER=https://your-analytics-mcp-server.com
SOCIAL_MCP_SERVER=https://your-social-mcp-server.com

# Optional MCP Authentication
MCP_API_KEY=your_mcp_api_key_here
MCP_JWT_SECRET=your_mcp_jwt_secret_here
```

#### Development Mode

For local development without MCP servers, set:

```
DEV_MODE=true  # Enables local implementations for vector storage, blockchain, and file storage
```

## LLM Integration

GigNova uses Groq's powerful LLM models for advanced text generation and structured outputs. The integration is implemented through the `langchain-groq` package.

### Using Groq Adapter

The Groq adapter is available as a singleton instance that can be imported and used throughout the codebase:

```python
from gignova.llm import groq_adapter

# Generate text
response = await groq_adapter.generate_text(
    prompt="Your prompt here",
    system_prompt="Optional system instructions",
    temperature=0.7
)

# Generate structured output
structured_response = await groq_adapter.generate_structured_output(
    prompt="Generate a job description",
    output_schema={"title": "str", "description": "str", "requirements": ["str"]}
)
```

### Configuration

The Groq adapter uses the `llama3-70b-8192` model by default. To use it, you need to:

1. Sign up for a Groq API key at [groq.com](https://groq.com)
2. Add your API key to the `.env` file:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Testing

### Running Tests

Run the full test suite with:

```bash
python -m pytest
```

The test suite includes:

1. **MCP Integration Tests**: Tests for all components using MCP servers (with mocked responses)
   - **MCPClientManager**: Asynchronous communication with MCP servers
   - **VectorManager**: Storing and retrieving embeddings via MCP vector server
   - **IPFSManager**: Storing and retrieving files via MCP storage server
   - **BlockchainManager**: Contract deployment and payment via MCP blockchain server
   - **QAAgent & PaymentAgent**: Agent functionality with MCP integration
   - **Orchestrator**: End-to-end job lifecycle with MCP integration

2. **Local Implementation Tests**: Tests for development mode with local implementations
   ```bash
   python -m pytest test_local_implementations.py -v
   ```

### Testing Local Implementations

For development mode, a test script is provided to verify the local implementations:

```bash
python test_local_implementations.py
```

This script tests:

1. **VectorManager**: Storing job and freelancer embeddings, and finding matching freelancers using semantic search
2. **IPFSManager**: Storing and retrieving files and JSON data using local file storage
3. **BlockchainManager**: Creating job contracts, checking status, completing jobs, and releasing payments

## Running the Application

### Production Mode (Default)

To run the application with MCP integration:

1. Ensure your MCP servers are running and accessible
2. Configure your `.env` file with the appropriate MCP server URLs
3. Start the server:
   ```bash
   python -m gignova.app
   ```

### Development Mode

To run the application with local implementations:

1. Set `DEV_MODE=true` in your `.env` file
2. Start the server:
   ```bash
   python -m gignova.app
   ```

### API Testing

To test the API endpoints:

1. Start the server (on a specific port if desired):
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

### Production Mode (Default)

For production deployment with MCP servers:

```
# Required settings
JWT_SECRET=your_jwt_secret_key
ENVIRONMENT=production

# Server configuration
PORT=8888  # Optional, defaults to 8888

# MCP server URLs
VECTOR_MCP_SERVER=https://your-vector-mcp-server.com
BLOCKCHAIN_MCP_SERVER=https://your-blockchain-mcp-server.com
STORAGE_MCP_SERVER=https://your-storage-mcp-server.com
ANALYTICS_MCP_SERVER=https://your-analytics-mcp-server.com
SOCIAL_MCP_SERVER=https://your-social-mcp-server.com
```

### Development Mode

For local development with in-memory implementations:

```
# Required settings
JWT_SECRET=your_jwt_secret_key
DEV_MODE=true
ENVIRONMENT=dev

# Server configuration
PORT=8889  # Optional, defaults to 8888
```

### Running the Application

#### Development Mode (Local Implementations)

```bash
DEV_MODE=true uvicorn gignova.app:app --reload
```

#### Production Mode (MCP Integration)

```bash
DEV_MODE=false uvicorn gignova.app:app --reload
```

The API will be available at http://localhost:8000

### Health Check

Verify that the application and MCP connections are working correctly:

```bash
curl http://localhost:8000/api/v1/health
```

This will return the status of the application and all MCP connections.

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
