#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="gignova",
    version="1.1.0",
    description="GigNova: The Self-Evolving Talent Ecosystem with MCP Integration",
    author="GigNova Team",
    author_email="info@gignova.io",
    packages=find_packages(where="backend"),
    package_dir={"": "backend"},
    python_requires=">=3.8",
    install_requires=[
        # Core Web Framework
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "python-multipart>=0.0.6",
        
        # Authentication & Security
        "pyjwt>=2.8.0",
        "passlib[bcrypt]>=1.7.4",
        "python-jose[cryptography]>=3.3.0",
        
        # AI/ML Dependencies
        "openai>=1.3.5",
        "sentence-transformers>=2.2.2",
        "torch>=2.1.1",
        "transformers>=4.35.2",
        "numpy>=1.24.3",
        "langchain-groq>=0.3.2",
        "groq>=0.28.0",
        
        # Blockchain & Web3
        "web3>=6.11.3",
        "eth-account>=0.9.0",
        "py-solc-x>=1.12.0",
        
        # Vector Database
        "qdrant-client>=1.6.9",
        
        # IPFS
        "ipfshttpclient>=0.8.0a2",
        
        # Environment & Configuration
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        
        # Background Tasks & Scheduling
        "schedule>=1.2.0",
        
        # MCP Integration
        "aiohttp>=3.9.1",
        "httpx>=0.25.2",
        "asyncio>=3.4.3",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "prod": [
            "gunicorn>=21.2.0",
            "prometheus-client>=0.19.0",
            "sentry-sdk[fastapi]>=1.38.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gignova=gignova.main:run_app",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
