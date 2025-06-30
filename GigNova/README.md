# GigNova: The Self-Evolving Talent Ecosystem

![GigNova Logo](https://via.placeholder.com/200x80?text=GigNova)

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🔗 Live Demo

**[Try GigNova Live](https://gignova-hybrid.netlify.app)** - Experience the platform with our hybrid API implementation

## 🚀 Overview

GigNova is a revolutionary blockchain-powered talent marketplace with autonomous AI agents that facilitate the entire freelance workflow. Our platform connects clients with skilled freelancers while leveraging cutting-edge AI to handle matching, negotiation, quality assurance, and payments. Built with a modular architecture for scalability and maintainability.

### ✨ Key Features

- **AI-Powered Matching**: Intelligent matching of freelancers to jobs based on skills, experience, and past performance
- **Autonomous Negotiation**: AI agents that help negotiate fair rates between clients and freelancers
- **Smart Contract Integration**: Blockchain-based escrow and payment system for secure transactions
- **Automated Quality Assurance**: AI-driven validation of deliverables against job requirements
- **Self-Evolving System**: Agents learn and improve from past interactions to optimize outcomes
- **Vector Storage**: Semantic search for finding the perfect talent match
- **Modular Architecture**: Clean separation of concerns with independent, interchangeable components

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.11+, Asyncio
- **AI/ML**: LangChain, Sentence Transformers, PyTorch
- **Vector Storage**: ChromaDB for embedding storage and retrieval
- **File Storage**: IPFS for decentralized file storage
- **Blockchain**: Ethereum for smart contracts and payments
- **Analytics**: Local event logging and metrics tracking
- **Authentication**: JWT

## 📋 Prerequisites

- Python 3.11+
- Sentence Transformers (all-MiniLM-L6-v2 model)
- Local ChromaDB instance (automatically created)
- Ethereum node (for blockchain functionality)
- IPFS node (for decentralized storage)

The application can run in two modes:
1. **Development Mode**: Uses local implementations with graceful degradation when services are unavailable
2. **Production Mode**: Requires all external services to be properly configured

## 🧪 Testing Status

- **Agent Tests**: ✅ All passing
- **Orchestrator Tests**: ✅ All passing
- **Model Tests**: ✅ All passing
- **API Tests**: ⚠️ Partially passing (some tests marked as xfail for future investigation)

### Recent Improvements

- Implemented hybrid job recommendations system with fallback to mock data when backend returns errors
- Fixed backend server port configuration to use port 8889 consistently
- Enhanced recommendation agent with improved feedback handling
- Added mock API functions for job recommendations and feedback
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

Create a `.env` file in the backend directory with the following variables:

```
# API Configuration
JWT_SECRET=your_jwt_secret_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Development Mode (enables local implementations)
DEV_MODE=true
ENVIRONMENT=dev

# Blockchain Configuration
ETHEREUM_PROVIDER_URL=http://localhost:8545
ETHEREUM_CHAIN_ID=1337
ETHEREUM_PRIVATE_KEY=your_private_key_here
ESCROW_CONTRACT_ADDRESS=your_contract_address_here

# Storage Configuration
IPFS_API_URL=/ip4/127.0.0.1/tcp/5001

# Agent Configuration
MATCHING_THRESHOLD=0.75
NEGOTIATION_MAX_ROUNDS=3
QA_THRESHOLD=0.8
```

> Note: For development purposes, the vector database (ChromaDB) is automatically created locally and doesn't require additional configuration.

## 🚀 Running the Application

### Starting Required Services

For full functionality, start the following services before running the application:

```bash
# Start a local Ethereum node (using Ganache or Hardhat)
ganache-cli

# Start a local IPFS node
ipfs daemon
```

### Development Server

```bash
cd backend
uvicorn gignova.app:app --reload
```

### Production Deployment with Gunicorn

```bash
cd backend
gunicorn gignova.app:app -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:8000
```

## 🧪 Running Tests

```bash
cd backend

# Run all tests
python -m pytest -xvs tests/

# Run core services tests
python -c "import test_core_services; import asyncio; asyncio.run(test_core_services.main())"
```

### Current Test Status

- **Vector Database**: ✅ PASSED
- **Blockchain**: ❌ FAILED (requires local Ethereum node)
- **Storage**: ❌ FAILED (requires local IPFS node)
- **Analytics**: ✅ PASSED
- **Orchestrator**: ✅ PASSED
- **Agents**: ✅ PASSED

## 📚 API Documentation

Once the server is running, access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🏗️ Project Structure

```
GigNova/
├── backend/
│   ├── gignova/
│   │   ├── agents/          # AI agent implementations
│   │   │   ├── base.py      # Base agent class
│   │   │   ├── matching.py  # Matching agent
│   │   │   ├── negotiation.py # Negotiation agent
│   │   │   ├── payment.py   # Payment agent
│   │   │   └── qa.py        # Quality assurance agent
│   │   ├── api/             # FastAPI routes and endpoints
│   │   ├── blockchain/      # Blockchain interfaces
│   │   │   └── manager.py   # Ethereum blockchain manager
│   │   ├── database/        # Vector DB and data storage
│   │   │   └── vector_manager.py # ChromaDB vector manager
│   │   ├── models/          # Data models and schemas
│   │   ├── storage/         # Storage management
│   │   │   └── manager.py   # IPFS storage manager
│   │   ├── utils/           # Utility functions and helpers
│   │   │   └── analytics.py # Analytics logger
│   │   ├── app.py           # FastAPI application
│   │   └── orchestrator.py  # Main orchestrator
│   ├── tests/               # Test suite
│   ├── test_core_services.py # Core services tests
│   └── setup.py             # Package setup
├── contracts/               # Solidity smart contracts
├── docs/                    # Documentation
├── tests/                   # Additional tests
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

- The LangChain team for their excellent framework
- The FastAPI team for their web framework
- The Ethereum community for blockchain infrastructure
- ChromaDB team for vector storage capabilities
- IPFS for decentralized storage solutions
- Sentence Transformers for embedding models

---