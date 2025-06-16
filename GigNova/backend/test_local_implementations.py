#!/usr/bin/env python3
"""
Test script for local implementations of vector database, file storage, and blockchain
"""

import os
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our local implementations
from gignova.database.vector_manager import VectorManager
from gignova.ipfs.manager import IPFSManager
from gignova.blockchain.manager import BlockchainManager
from gignova.config.settings import Settings

def test_vector_manager():
    """Test the in-memory vector database implementation"""
    logger.info("Testing VectorManager...")
    
    # Initialize vector manager
    vector_manager = VectorManager()
    
    # Store job embedding
    job_id = "test-job-123"
    job_text = "Senior Python Developer with FastAPI and ML experience"
    job_metadata = {"budget_range": [80, 120]}
    
    vector_manager.store_job_embedding(job_id, job_text, job_metadata)
    logger.info(f"Stored job embedding for job_id: {job_id}")
    
    # Store freelancer embedding
    freelancer_id = "test-freelancer-456"
    freelancer_text = "Python developer with 5 years of experience in FastAPI and machine learning"
    freelancer_metadata = {"hourly_rate": 100}
    
    vector_manager.store_freelancer_embedding(freelancer_id, freelancer_text, freelancer_metadata)
    logger.info(f"Stored freelancer embedding for freelancer_id: {freelancer_id}")
    
    # Search for matching freelancers
    query = "Need a Python developer with ML experience"
    results = vector_manager.find_matches(query, limit=5)
    
    logger.info(f"Search results for '{query}':")
    for result in results:
        logger.info(f"  Freelancer ID: {result['freelancer_id']}, Score: {result['score']}")
    
    return len(results) > 0

def test_ipfs_manager():
    """Test the local file storage implementation"""
    logger.info("Testing IPFSManager (local file storage)...")
    
    # Initialize IPFS manager
    ipfs_manager = IPFSManager()
    
    # Store file
    test_data = b"This is a test file for local storage"
    file_hash = ipfs_manager.store_deliverable(test_data)
    logger.info(f"Stored test file with hash: {file_hash}")
    
    # Retrieve file
    retrieved_data = ipfs_manager.retrieve_deliverable(file_hash)
    logger.info(f"Retrieved file content: {retrieved_data.decode('utf-8')}")
    
    # Store JSON by converting it to bytes
    test_json = {"name": "Test User", "role": "Developer"}
    json_bytes = json.dumps(test_json).encode('utf-8')
    json_hash = ipfs_manager.store_deliverable(json_bytes)
    logger.info(f"Stored JSON with hash: {json_hash}")
    
    # Retrieve JSON
    retrieved_json_bytes = ipfs_manager.retrieve_deliverable(json_hash)
    retrieved_json = json.loads(retrieved_json_bytes.decode('utf-8'))
    logger.info(f"Retrieved JSON: {retrieved_json}")
    
    # Check storage directory
    storage_path = Path(os.path.expanduser('~')) / '.gignova' / 'storage'
    logger.info(f"Storage directory: {storage_path}")
    logger.info(f"Files in storage: {list(storage_path.glob('*'))}")
    
    return retrieved_data == test_data and retrieved_json == test_json

def test_blockchain_manager():
    """Test the local blockchain implementation"""
    logger.info("Testing BlockchainManager (local implementation)...")
    
    # Initialize blockchain manager
    blockchain_manager = BlockchainManager()
    
    # Create job contract
    job_id = "test-job-789"
    client = "client-123"
    freelancer = "freelancer-456"
    amount = 500
    ipfs_hash = "test-hash-abc"
    
    contract_id = blockchain_manager.create_escrow(job_id, client, freelancer, amount, ipfs_hash)
    logger.info(f"Created contract with ID: {contract_id}")
    
    # Get contract status
    contract_status = blockchain_manager.blockchain.contracts.get(contract_id, {}).get("status")
    logger.info(f"Contract status: {contract_status}")
    
    # Complete job
    success = blockchain_manager.blockchain.complete_job(contract_id)
    logger.info(f"Job completion success: {success}")
    
    # Get updated status
    contract_status = blockchain_manager.blockchain.contracts.get(contract_id, {}).get("status")
    logger.info(f"Contract status after completion: {contract_status}")
    
    # Release payment
    success = blockchain_manager.release_payment(job_id)
    logger.info(f"Payment release success: {success}")
    
    # Check blockchain directory
    blockchain_path = Path(os.path.expanduser('~')) / '.gignova' / 'blockchain'
    logger.info(f"Blockchain directory: {blockchain_path}")
    logger.info(f"Files in blockchain dir: {list(blockchain_path.glob('*'))}")
    
    # Check contracts file
    contracts_file = blockchain_path / 'contracts.json'
    if contracts_file.exists():
        with open(contracts_file, 'r') as f:
            contracts = json.load(f)
        logger.info(f"Contracts: {contracts}")
    
    return contract_id and success

def main():
    """Run all tests"""
    logger.info("Starting tests for local implementations...")
    logger.info(f"DEV_MODE is {'enabled' if Settings.DEV_MODE else 'disabled'}")
    
    vector_success = test_vector_manager()
    logger.info(f"Vector Manager test {'passed' if vector_success else 'failed'}")
    
    ipfs_success = test_ipfs_manager()
    logger.info(f"IPFS Manager test {'passed' if ipfs_success else 'failed'}")
    
    blockchain_success = test_blockchain_manager()
    logger.info(f"Blockchain Manager test {'passed' if blockchain_success else 'failed'}")
    
    if vector_success and ipfs_success and blockchain_success:
        logger.info("All tests passed! Local implementations are working correctly.")
    else:
        logger.error("Some tests failed. Check the logs for details.")

if __name__ == "__main__":
    main()
