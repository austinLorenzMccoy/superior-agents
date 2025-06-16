# GigNova: The Self-Evolving Talent Ecosystem

![GigNova Logo](https://via.placeholder.com/200x80?text=GigNova)

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Overview

GigNova is a revolutionary blockchain-powered talent marketplace with autonomous AI agents that facilitate the entire freelance workflow. Our platform connects clients with skilled freelancers while leveraging cutting-edge AI to handle matching, negotiation, quality assurance, and payments.

### ✨ Key Features

- **AI-Powered Matching**: Intelligent matching of freelancers to jobs based on skills, experience, and past performance
- **Autonomous Negotiation**: AI agents that help negotiate fair rates between clients and freelancers
- **Smart Contract Integration**: Blockchain-based escrow and payment system for secure transactions
- **Automated Quality Assurance**: AI-driven validation of deliverables against job requirements
- **Self-Evolving System**: Agents learn and improve from past interactions to optimize outcomes
- **Vector Storage**: Semantic search for finding the perfect talent match

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.8+
- **AI/ML**: OpenAI, Sentence Transformers, PyTorch
- **Vector Storage**: In-memory implementation with NumPy
- **File Storage**: Local filesystem with content addressing
- **Blockchain**: Local JSON-based implementation
- **Authentication**: JWT

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key

No external services required! The application uses simplified local implementations for:
- Vector storage (instead of Qdrant)
- File storage (instead of IPFS)
- Blockchain functionality (instead of Ethereum)

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

# Blockchain
WEB3_PROVIDER_URI=https://mainnet.infura.io/v3/your_infura_key
WALLET_PRIVATE_KEY=your_wallet_private_key

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key

# IPFS
IPFS_API_URL=/ip4/127.0.0.1/tcp/5001
```

## 🚀 Running the Application

### Development Server

```bash
uvicorn gignova.main:app --reload
```

### Production Server

```bash
gunicorn -k uvicorn.workers.UvicornWorker -w 4 gignova.main:app
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
│   │   ├── api/             # FastAPI routes and endpoints
│   │   ├── blockchain/      # Blockchain and smart contract interfaces
│   │   ├── config/          # Configuration management
│   │   ├── database/        # Vector DB and data storage
│   │   ├── ipfs/            # IPFS storage management
│   │   ├── models/          # Data models and schemas
│   │   └── utils/           # Utility functions and helpers
│   └── tests/               # Test suite
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
