# GigNova: The Self-Evolving Talent Ecosystem with MCP Integration

![GigNova Logo](https://via.placeholder.com/200x80?text=GigNova)

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-Integrated-purple)](https://github.com/yourusername/gignova)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Overview

GigNova is a revolutionary blockchain-powered talent marketplace with autonomous AI agents that facilitate the entire freelance workflow. Our platform connects clients with skilled freelancers while leveraging cutting-edge AI to handle matching, negotiation, quality assurance, and payments. Now enhanced with MCP (Model Context Protocol) integration for production-grade scalability and interoperability.

### ✨ Key Features

- **AI-Powered Matching**: Intelligent matching of freelancers to jobs based on skills, experience, and past performance
- **Autonomous Negotiation**: AI agents that help negotiate fair rates between clients and freelancers
- **Smart Contract Integration**: Blockchain-based escrow and payment system for secure transactions
- **Automated Quality Assurance**: AI-driven validation of deliverables against job requirements
- **Self-Evolving System**: Agents learn and improve from past interactions to optimize outcomes
- **Vector Storage**: Semantic search for finding the perfect talent match
- **MCP Integration**: Standardized protocol for AI service interoperability across vector storage, blockchain, file storage, analytics, and social media

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.11+, Asyncio
- **AI/ML**: OpenAI, Groq, Sentence Transformers, PyTorch
- **Vector Storage**: MCP Vector Server (production) / In-memory implementation (development)
- **File Storage**: MCP Storage Server (production) / Local filesystem (development)
- **Blockchain**: MCP Blockchain Server (production) / Local JSON-based implementation (development)
- **Analytics**: MCP Analytics Server for event logging and metrics
- **Authentication**: JWT
- **MCP Protocol**: Standardized API for AI service interoperability

## 📋 Prerequisites

- Python 3.11+
- OpenAI API key or Groq API key
- MCP Servers (for production mode)

The application can run in two modes:
1. **Development Mode**: Uses simplified local implementations for vector storage, file storage, and blockchain functionality
2. **Production Mode**: Uses MCP servers for all external services including vector storage, blockchain, file storage, analytics, and social media integration

## 🧪 Testing Status

- **Agent Tests**: ✅ All passing
- **Orchestrator Tests**: ✅ All passing
- **Model Tests**: ✅ All passing
- **API Tests**: ⚠️ Partially passing (some tests marked as xfail for future investigation)

### Recent Improvements

- Fixed async handling in agent and API tests
- Updated negotiation agent logic to correctly handle cases where freelancer rates are far above client budget
- Added user_id property to FreelancerProfile model for API compatibility
- Updated Pydantic validators to V2 style field_validators
- Added Groq adapter for LLM API integration

## 🔧 Installation

### Option 1: Using Docker (Recommended)

The easiest way to run GigNova is using Docker and Docker Compose:

```bash
# Clone the repository
git clone https://github.com/yourusername/gignova.git
cd gignova

# Start the application using Docker Compose
docker-compose up -d

# Access the API at http://localhost:8889
```

### Option 2: Manual Setup

#### Clone the repository

```bash
git clone https://github.com/yourusername/gignova.git
cd gignova
```

#### Set up a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install the package

```bash
pip install -e ".[dev]"
```

### Environment Variables

Create a `.env` file in the project root with the following variables:

```
# API Configuration
JWT_SECRET=your_jwt_secret_key

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Development Mode (set to False for production with MCP)
DEV_MODE=True

# MCP Server URLs (required for production mode)
VECTOR_MCP_SERVER=http://vector-mcp-server:8080
BLOCKCHAIN_MCP_SERVER=http://blockchain-mcp-server:8081
STORAGE_MCP_SERVER=http://storage-mcp-server:8082
ANALYTICS_MCP_SERVER=http://analytics-mcp-server:8083
SOCIAL_MCP_SERVER=http://social-mcp-server:8084

# MCP Authentication (if required)
MCP_API_KEY=your_mcp_api_key
MCP_JWT_SECRET=your_mcp_jwt_secret

# Legacy Configuration (for development mode)
WEB3_PROVIDER_URI=https://mainnet.infura.io/v3/your_infura_key
WALLET_PRIVATE_KEY=your_wallet_private_key
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key
IPFS_API_URL=/ip4/127.0.0.1/tcp/5001
```

## 🚀 Running the Application

### Development Server (Local Implementations)

```bash
uvicorn gignova.app:app --reload
```

### Production Server (MCP Integration)

```bash
# First ensure all MCP server URLs are set in .env
export DEV_MODE=False
uvicorn gignova.app_mcp:app --host 0.0.0.0 --port 8888
```

### Production Deployment with Gunicorn

```bash
export DEV_MODE=False
gunicorn -k uvicorn.workers.UvicornWorker -w 4 gignova.app_mcp:app
```

## 🧪 Testing

Run the test suite with pytest:

```bash
pytest
```

Run tests with coverage report:

```bash
pytest --cov=gignova
```

## 📚 API Documentation

Once the server is running, access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🏗️ Project Structure

```
gignova/
├── backend/
│   ├── gignova/
│   │   ├── agents/          # AI agent implementations
│   │   │   ├── base.py      # Base agent with MCP integration
│   │   │   ├── qa.py        # QA agent with MCP integration
│   │   │   └── payment.py   # Payment agent with MCP integration
│   │   ├── api/             # FastAPI routes and endpoints
│   │   ├── blockchain/      # Blockchain interfaces
│   │   │   └── manager_mcp.py # MCP blockchain manager
│   │   ├── config/          # Configuration management
│   │   ├── database/        # Vector DB and data storage
│   │   │   └── vector_manager_mcp.py # MCP vector manager
│   │   ├── ipfs/            # Storage management
│   │   │   └── manager_mcp.py # MCP storage manager
│   │   ├── mcp/             # MCP integration
│   │   │   ├── __init__.py  # MCP module initialization
│   │   │   └── client.py    # MCP client manager
│   │   ├── models/          # Data models and schemas
│   │   ├── utils/           # Utility functions and helpers
│   │   ├── app.py           # Development mode application
│   │   ├── app_mcp.py       # Production mode application with MCP
│   │   ├── orchestrator.py  # Development orchestrator
│   │   └── orchestrator_mcp.py # Production orchestrator with MCP
│   └── tests/               # Test suite
│       └── test_mcp_integration.py # MCP integration tests
├── contracts/               # Solidity smart contracts
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── setup.py                 # Package setup
├── pyproject.toml           # Project configuration
└── README.md                # This file
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- OpenAI for their powerful language models
- The FastAPI team for their excellent framework
- The Ethereum community for blockchain infrastructure
- Qdrant team for vector search capabilities
- IPFS for decentralized storage solutions

---

<p align="center">
  Built with ❤️ by the GigNova Team
</p>
