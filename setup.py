#!/usr/bin/env python3
"""
AutoTradeX Setup and Installation Script
This is a minimal setup.py that defers to pyproject.toml for package metadata.
It also provides utility functions for initial setup, API key validation, and system checks.
"""

import os
import sys
import subprocess
import requests
from pathlib import Path
import json
from setuptools import setup

# Defer to pyproject.toml for package metadata
setup()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required. Current version:", sys.version)
        return False
    print("✅ Python version check passed")
    return True

def install_package():
    """Install package in development mode"""
    print("📦 Installing AutoTradeX...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], 
                      check=True, capture_output=True)
        print("✅ AutoTradeX installed successfully in development mode")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install package: {e}")
        return False

def setup_environment():
    """Set up environment file"""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_example.exists():
        print("❌ .env.example file not found!")
        return False
    
    if env_file.exists():
        print("⚠️  .env file already exists")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("📝 Using existing .env file")
            return True
    
    # Copy example to .env
    with open(env_example, 'r') as f:
        content = f.read()
    
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("📝 Created .env file from template")
    return True

def validate_api_keys():
    """Validate API keys"""
    from dotenv import load_dotenv
    load_dotenv()
    
    print("🔑 Validating API keys...")
    
    # Check Groq API
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key or groq_key == "your_groq_api_key_here":
        print("❌ GROQ_API_KEY not set. Get one at: https://console.groq.com/")
        return False
    
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        # Test API call
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello"}],
            model="llama3-8b-8192",
            max_tokens=10
        )
        print("✅ Groq API key validated")
    except Exception as e:
        print(f"❌ Groq API validation failed: {e}")
        return False
    
    # Check Qdrant
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url or qdrant_url == "https://your-cluster-url.qdrant.io":
        print("❌ QDRANT_URL not set. Get free cluster at: https://cloud.qdrant.io/")
        return False
    
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url=qdrant_url, api_key=os.getenv("QDRANT_API_KEY"))
        collections = client.get_collections()
        print("✅ Qdrant connection validated")
    except Exception as e:
        print(f"❌ Qdrant validation failed: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up AutoTradeX...")
    
    if not check_python_version():
        sys.exit(1)
    
    if not setup_environment():
        sys.exit(1)
    
    if not install_package():
        sys.exit(1)
    
    if not validate_api_keys():
        print("⚠️  API key validation failed. Update your .env file and try again.")
        sys.exit(1)
    
    print("✅ AutoTradeX setup complete! Run 'python -m autotradex' to start.")

if __name__ == "__main__":
    main()
