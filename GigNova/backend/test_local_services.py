#!/usr/bin/env python3
"""
Test script for local service implementations
Verifies that local storage and blockchain implementations work correctly
"""

import asyncio
import logging
import os
import sys
import json
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure DEV_MODE is set for testing
os.environ["DEV_MODE"] = "true"

async def test_local_storage():
    """Test local storage implementation"""
    logger.info("Testing local storage implementation...")
    
    try:
        from gignova.utils.service_factory import service_factory
        
        # Get local storage manager
        storage_manager = service_factory.get_storage_manager(use_local=True)
        
        # Test connection
        connected = await storage_manager.connect()
        logger.info(f"Storage connection: {'SUCCESS' if connected else 'FAILED'}")
        
        # Test storing a file
        test_data = {
            "content": "This is a test file for GigNova local storage",
            "metadata": {
                "test": True,
                "timestamp": "2023-06-24T12:00:00Z"
            }
        }
        
        store_result = await storage_manager.store_file(
            file_data=json.dumps(test_data),
            metadata={"content_type": "application/json", "test": True}
        )
        
        if store_result.get("success"):
            cid = store_result.get("cid")
            logger.info(f"File stored successfully with CID: {cid}")
            
            # Test retrieving the file
            retrieve_result = await storage_manager.retrieve_file(cid)
            
            if retrieve_result.get("success"):
                data = retrieve_result.get("data")
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                
                logger.info(f"File retrieved successfully: {data[:50]}...")
                
                # Test pinning the file
                pin_result = await storage_manager.pin_file(cid)
                
                if pin_result.get("success"):
                    logger.info(f"File pinned successfully")
                    
                    # Test listing pins
                    pins_result = await storage_manager.list_pins()
                    
                    if pins_result.get("success"):
                        pins = pins_result.get("pins", [])
                        logger.info(f"Pins listed successfully: {pins}")
                        
                        if cid in pins:
                            logger.info("LOCAL STORAGE TEST: ✅ PASSED")
                            return True
                        else:
                            logger.error(f"CID {cid} not found in pins")
                    else:
                        logger.error(f"Failed to list pins: {pins_result.get('error')}")
                else:
                    logger.error(f"Failed to pin file: {pin_result.get('error')}")
            else:
                logger.error(f"Failed to retrieve file: {retrieve_result.get('error')}")
        else:
            logger.error(f"Failed to store file: {store_result.get('error')}")
    
    except Exception as e:
        logger.error(f"Local storage test failed with exception: {e}")
    
    logger.error("LOCAL STORAGE TEST: ❌ FAILED")
    return False

async def test_local_blockchain():
    """Test local blockchain implementation"""
    logger.info("Testing local blockchain implementation...")
    
    try:
        from gignova.utils.service_factory import service_factory
        
        # Get local blockchain manager
        blockchain_manager = service_factory.get_blockchain_manager(use_local=True)
        
        # Test connection
        connected = await blockchain_manager.connect()
        logger.info(f"Blockchain connection: {'SUCCESS' if connected else 'FAILED'}")
        
        # Test creating an escrow
        escrow_result = await blockchain_manager.create_escrow(
            client_id="client123",
            freelancer_id="freelancer456",
            amount=1.5,
            deadline=30 * 24 * 60 * 60  # 30 days in seconds
        )
        
        if escrow_result.get("success"):
            contract_address = escrow_result.get("contract_address")
            tx_hash = escrow_result.get("transaction_hash")
            logger.info(f"Escrow created successfully: {contract_address}")
            
            # Test getting transaction status
            tx_status = await blockchain_manager.get_transaction_status(tx_hash)
            
            if tx_status.get("success"):
                logger.info(f"Transaction status: {tx_status.get('status')}")
                
                # Test releasing payment
                release_result = await blockchain_manager.release_payment(contract_address)
                
                if release_result.get("success"):
                    release_tx_hash = release_result.get("transaction_hash")
                    logger.info(f"Payment released successfully: {release_tx_hash}")
                    
                    # Test getting transaction status for release
                    release_tx_status = await blockchain_manager.get_transaction_status(release_tx_hash)
                    
                    if release_tx_status.get("success"):
                        logger.info(f"Release transaction status: {release_tx_status.get('status')}")
                        logger.info("LOCAL BLOCKCHAIN TEST: ✅ PASSED")
                        return True
                    else:
                        logger.error(f"Failed to get release transaction status: {release_tx_status.get('error')}")
                else:
                    logger.error(f"Failed to release payment: {release_result.get('error')}")
            else:
                logger.error(f"Failed to get transaction status: {tx_status.get('error')}")
        else:
            logger.error(f"Failed to create escrow: {escrow_result.get('error')}")
    
    except Exception as e:
        logger.error(f"Local blockchain test failed with exception: {e}")
    
    logger.error("LOCAL BLOCKCHAIN TEST: ❌ FAILED")
    return False

async def test_vector_manager():
    """Test vector manager implementation"""
    logger.info("Testing vector manager implementation...")
    
    try:
        # Set a timeout for the vector manager test
        async def _run_test():
            from gignova.utils.service_factory import service_factory
            
            # Get vector manager
            vector_manager = service_factory.get_vector_manager()
            
            # Test generating embeddings
            text = "This is a test text for embedding generation"
            embedding = await vector_manager.generate_embedding(text)
            
            if embedding is not None and len(embedding) > 0:
                logger.info(f"Embedding generated successfully with dimension: {len(embedding)}")
                return True
            else:
                logger.error("Failed to generate embedding")
                return False
        
        # Run the test with a timeout
        try:
            # Set a 30-second timeout
            result = await asyncio.wait_for(_run_test(), timeout=30)
            if result:
                logger.info("VECTOR MANAGER TEST: ✅ PASSED")
                return True
        except asyncio.TimeoutError:
            logger.error("Vector manager test timed out after 30 seconds")
    
    except Exception as e:
        logger.error(f"Vector manager test failed with exception: {e}")
    
    logger.error("VECTOR MANAGER TEST: ❌ FAILED")
    return False

async def main():
    """Run all tests"""
    logger.info("Starting local service tests...")
    
    # Test results
    results = {
        "local_storage": False,
        "local_blockchain": False,
        "vector_manager": False
    }
    
    # Run tests
    results["local_storage"] = await test_local_storage()
    results["local_blockchain"] = await test_local_blockchain()
    results["vector_manager"] = await test_vector_manager()
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{test_name.upper()}: {status}")
    
    logger.info("="*50)
    
    # Return overall success
    return all(results.values())

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
