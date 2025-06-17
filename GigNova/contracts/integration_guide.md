# GigNova Contract Integration Guide

This guide explains how to integrate the GigNova backend with the updated smart contract implementation.

## Overview

The new `GigNovaContract.sol` has been designed to align with the backend's `LocalBlockchain` implementation. It uses the same job status constants and similar contract structure to ensure compatibility.

### Job Status Constants

Both implementations use the following job status constants:
- `created` - Initial state when a job contract is created
- `completed` - Job has been marked as completed by the client
- `disputed` - Job has a dispute that needs resolution
- `paid` - Payment has been released to the freelancer

## Backend Integration

To integrate the backend with the smart contract, follow these steps:

### 1. Deploy the Smart Contract

```bash
cd /Users/a/Documents/Agrlab/superior-agents/GigNova/contracts
npx hardhat run scripts/deploy_gignova_contract.js --network <network>
```

Save the deployed contract address for use in the backend.

### 2. Create a Web3 Integration Module

Create a new file in the backend at `/Users/a/Documents/Agrlab/superior-agents/GigNova/backend/gignova/blockchain/web3_manager.py`:

```python
#!/usr/bin/env python3
"""
GigNova: Web3 Blockchain Manager
"""

import os
import time
import json
import logging
from typing import Dict, Optional, List
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Configure logging
logger = logging.getLogger(__name__)

# Job status constants (matching smart contract)
JOB_STATUS_CREATED = "created"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_DISPUTED = "disputed"
JOB_STATUS_PAID = "paid"

class Web3BlockchainManager:
    """Web3 blockchain implementation for GigNova"""
    
    def __init__(self, rpc_url: str, contract_address: str, private_key: str):
        """Initialize the Web3 blockchain manager"""
        # Connect to Ethereum node
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Load contract ABI
        contract_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                   'contracts', 'artifacts', 'src', 'GigNovaContract.sol', 'GigNovaContract.json')
        with open(contract_dir, 'r') as f:
            contract_json = json.load(f)
            self.contract_abi = contract_json['abi']
        
        # Initialize contract
        self.contract_address = contract_address
        self.contract = self.web3.eth.contract(address=contract_address, abi=self.contract_abi)
        
        # Set account
        self.private_key = private_key
        self.account = self.web3.eth.account.from_key(private_key)
        self.address = self.account.address
        
        logger.info(f"Initialized Web3 blockchain manager with contract at {contract_address}")
    
    def create_escrow(self, job_id: str, client: str, freelancer: str, amount: float, ipfs_hash: str) -> str:
        """Create escrow for a job"""
        try:
            # Convert amount to wei
            amount_wei = self.web3.to_wei(amount, 'ether')
            
            # Build transaction
            tx = self.contract.functions.createJob(
                job_id,
                freelancer,
                ipfs_hash
            ).build_transaction({
                'from': self.address,
                'value': amount_wei,
                'gas': 2000000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.address)
            })
            
            # Sign and send transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Extract contract ID from event logs
            contract_id = ""
            for log in receipt['logs']:
                try:
                    event = self.contract.events.JobCreated().process_log(log)
                    contract_id = event['args']['contractId']
                    break
                except:
                    continue
            
            logger.info(f"Created job contract {contract_id} for job {job_id}")
            return contract_id
            
        except Exception as e:
            logger.error(f"Escrow creation failed: {e}")
            return ""
    
    def complete_job(self, job_id: str) -> bool:
        """Mark a job as completed"""
        try:
            # Get contract ID for job
            contract_id = self._get_contract_id_for_job(job_id)
            if not contract_id:
                logger.error(f"No contract found for job {job_id}")
                return False
            
            # Build transaction
            tx = self.contract.functions.completeJob(contract_id).build_transaction({
                'from': self.address,
                'gas': 2000000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.address)
            })
            
            # Sign and send transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(f"Marked contract {contract_id} as completed")
            return True
            
        except Exception as e:
            logger.error(f"Job completion failed: {e}")
            return False
    
    def release_payment(self, job_id: str) -> bool:
        """Release payment for a job"""
        try:
            # Get contract ID for job
            contract_id = self._get_contract_id_for_job(job_id)
            if not contract_id:
                logger.error(f"No contract found for job {job_id}")
                return False
            
            # Build transaction
            tx = self.contract.functions.releasePayment(contract_id).build_transaction({
                'from': self.address,
                'gas': 2000000,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.address)
            })
            
            # Sign and send transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for transaction receipt
            self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(f"Released payment for contract {contract_id}")
            return True
            
        except Exception as e:
            logger.error(f"Payment release failed: {e}")
            return False
    
    def get_contract_status(self, job_id: str) -> Optional[Dict]:
        """Get the status of a contract for a job"""
        try:
            # Get contract ID for job
            contract_id = self._get_contract_id_for_job(job_id)
            if not contract_id:
                logger.warning(f"No contract found for job {job_id}")
                return None
            
            # Get contract details
            contract = self.contract.functions.getContract(contract_id).call()
            
            # Convert to dictionary format matching LocalBlockchain
            return {
                "job_id": contract[0],
                "client": contract[1],
                "freelancer": contract[2],
                "amount": self.web3.from_wei(contract[3], 'ether'),
                "ipfs_hash": contract[4],
                "status": contract[5],
                "created_at": contract[6]
            }
            
        except Exception as e:
            logger.error(f"Get contract status failed: {e}")
            return None
    
    def _get_contract_id_for_job(self, job_id: str) -> str:
        """Find contract ID for a job"""
        try:
            return self.contract.functions.getContractIdForJob(job_id).call()
        except Exception as e:
            logger.error(f"Failed to get contract ID for job {job_id}: {e}")
            return ""
```

### 3. Update the BlockchainManager Class

Modify the `BlockchainManager` class in `/Users/a/Documents/Agrlab/superior-agents/GigNova/backend/gignova/blockchain/manager.py` to use either the local implementation or the Web3 implementation based on configuration:

```python
class BlockchainManager:
    def __init__(self, use_web3=False, rpc_url=None, contract_address=None, private_key=None):
        """Initialize the blockchain manager with local or Web3 implementation"""
        if use_web3 and rpc_url and contract_address and private_key:
            from .web3_manager import Web3BlockchainManager
            self.blockchain = Web3BlockchainManager(rpc_url, contract_address, private_key)
            logger.info("Initialized blockchain manager with Web3 implementation")
        else:
            self.blockchain = LocalBlockchain()
            logger.info("Initialized blockchain manager with local implementation")
```

### 4. Update Configuration

Add the following configuration options to your environment file:

```
# Blockchain settings
USE_WEB3=false
RPC_URL=http://localhost:8545
CONTRACT_ADDRESS=0x...
PRIVATE_KEY=0x...
```

## Testing the Integration

You can test the integration using the provided test script:

```bash
cd /Users/a/Documents/Agrlab/superior-agents/GigNova/contracts
npx hardhat run scripts/test_gignova_contract.js --network localhost
```

## Contract Functions

The `GigNovaContract` provides the following functions:

1. `createJob(string jobId, address freelancer, string ipfsHash) payable returns (string)` - Creates a new job contract
2. `completeJob(string contractId)` - Marks a job as completed
3. `releasePayment(string contractId)` - Releases payment to the freelancer
4. `createDispute(string contractId)` - Creates a dispute for a job
5. `resolveDispute(string contractId, uint16 clientShare)` - Resolves a dispute with specified fund distribution
6. `getContract(string contractId) view returns (JobContract)` - Gets contract details by ID
7. `getContractIdForJob(string jobId) view returns (string)` - Gets contract ID for a job

## Events

The contract emits the following events:

1. `JobCreated(string contractId, string jobId, address client, address freelancer, uint256 amount)`
2. `JobCompleted(string contractId, string jobId)`
3. `PaymentReleased(string contractId, string jobId, uint256 amount)`
4. `JobDisputed(string contractId, string jobId)`
5. `FeePercentChanged(uint16 newFeePercent)`
