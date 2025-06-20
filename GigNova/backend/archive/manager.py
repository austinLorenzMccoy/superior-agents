#!/usr/bin/env python3
"""
GigNova: Local Blockchain Manager (Simplified Implementation)
"""

import os
import time
import json
import logging
import uuid
from pathlib import Path
from typing import Dict, Optional, List

# Configure logging
logger = logging.getLogger(__name__)

# Job status constants
JOB_STATUS_CREATED = "created"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_DISPUTED = "disputed"
JOB_STATUS_PAID = "paid"

class LocalBlockchain:
    """Simple local blockchain implementation"""
    
    def __init__(self):
        # Create storage directory
        self.storage_dir = Path(os.path.expanduser('~')) / '.gignova' / 'blockchain'
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize blockchain state
        self.contracts_file = self.storage_dir / 'contracts.json'
        self.transactions_file = self.storage_dir / 'transactions.json'
        
        # Load or create contracts data
        if self.contracts_file.exists():
            with open(self.contracts_file, 'r') as f:
                self.contracts = json.load(f)
        else:
            self.contracts = {}
            self._save_contracts()
        
        # Load or create transactions data
        if self.transactions_file.exists():
            with open(self.transactions_file, 'r') as f:
                self.transactions = json.load(f)
        else:
            self.transactions = []
            self._save_transactions()
        
        logger.info(f"Initialized local blockchain at {self.storage_dir}")
    
    def _save_contracts(self):
        """Save contracts to file"""
        with open(self.contracts_file, 'w') as f:
            json.dump(self.contracts, f, indent=2)
    
    def _save_transactions(self):
        """Save transactions to file"""
        with open(self.transactions_file, 'w') as f:
            json.dump(self.transactions, f, indent=2)
    
    def create_job(self, job_id: str, client: str, freelancer: str, amount: float, ipfs_hash: str) -> str:
        """Create a new job contract"""
        contract_id = str(uuid.uuid4())
        
        # Create contract
        self.contracts[contract_id] = {
            "job_id": job_id,
            "client": client,
            "freelancer": freelancer,
            "amount": amount,
            "ipfs_hash": ipfs_hash,
            "status": JOB_STATUS_CREATED,
            "created_at": time.time()
        }
        
        # Record transaction
        self.transactions.append({
            "type": "create_job",
            "contract_id": contract_id,
            "job_id": job_id,
            "timestamp": time.time()
        })
        
        # Save changes
        self._save_contracts()
        self._save_transactions()
        
        logger.info(f"Created job contract {contract_id} for job {job_id}")
        return contract_id
    
    def complete_job(self, contract_id: str) -> bool:
        """Mark a job as completed"""
        if contract_id not in self.contracts:
            logger.error(f"Contract {contract_id} not found")
            return False
        
        # Update contract status
        self.contracts[contract_id]["status"] = JOB_STATUS_COMPLETED
        
        # Record transaction
        self.transactions.append({
            "type": "complete_job",
            "contract_id": contract_id,
            "job_id": self.contracts[contract_id]["job_id"],
            "timestamp": time.time()
        })
        
        # Save changes
        self._save_contracts()
        self._save_transactions()
        
        logger.info(f"Marked contract {contract_id} as completed")
        return True
    
    def release_payment(self, contract_id: str) -> bool:
        """Release payment for a job"""
        if contract_id not in self.contracts:
            logger.error(f"Contract {contract_id} not found")
            return False
        
        # Check if job is completed
        if self.contracts[contract_id]["status"] != JOB_STATUS_COMPLETED:
            logger.error(f"Cannot release payment for job that is not completed")
            return False
        
        # Update contract status
        self.contracts[contract_id]["status"] = JOB_STATUS_PAID
        
        # Record transaction
        self.transactions.append({
            "type": "release_payment",
            "contract_id": contract_id,
            "job_id": self.contracts[contract_id]["job_id"],
            "amount": self.contracts[contract_id]["amount"],
            "timestamp": time.time()
        })
        
        # Save changes
        self._save_contracts()
        self._save_transactions()
        
        logger.info(f"Released payment for contract {contract_id}")
        return True


class BlockchainManager:
    def __init__(self):
        """Initialize the blockchain manager with local implementation"""
        self.blockchain = LocalBlockchain()
        logger.info("Initialized blockchain manager with local implementation")
    
    def _get_contract_id_for_job(self, job_id: str) -> Optional[str]:
        """Find contract ID for a job"""
        for contract_id, contract in self.blockchain.contracts.items():
            if contract["job_id"] == job_id:
                return contract_id
        return None
    
    def create_escrow(self, job_id: str, client: str, freelancer: str, amount: float, ipfs_hash: str) -> str:
        """Create escrow for a job"""
        try:
            # Check if a contract already exists for this job
            existing_contract_id = self._get_contract_id_for_job(job_id)
            if existing_contract_id:
                logger.warning(f"Contract already exists for job {job_id}: {existing_contract_id}")
                return existing_contract_id
            
            # Create new contract
            contract_id = self.blockchain.create_job(job_id, client, freelancer, amount, ipfs_hash)
            return contract_id
            
        except Exception as e:
            logger.error(f"Escrow creation failed: {e}")
            return ""
    
    def release_payment(self, job_id: str) -> bool:
        """Release payment from escrow"""
        try:
            # Find contract for this job
            contract_id = self._get_contract_id_for_job(job_id)
            if not contract_id:
                logger.error(f"No contract found for job {job_id}")
                return False
            
            # Release payment
            return self.blockchain.release_payment(contract_id)
            
        except Exception as e:
            logger.error(f"Payment release failed: {e}")
            return False
    
    def complete_job(self, job_id: str) -> bool:
        """Mark a job as completed"""
        try:
            # Find contract for this job
            contract_id = self._get_contract_id_for_job(job_id)
            if not contract_id:
                logger.error(f"No contract found for job {job_id}")
                return False
            
            # Complete job
            return self.blockchain.complete_job(contract_id)
            
        except Exception as e:
            logger.error(f"Job completion failed: {e}")
            return False
    
    def get_contract_status(self, job_id: str) -> Optional[Dict]:
        """Get the status of a contract for a job"""
        try:
            # Find contract for this job
            contract_id = self._get_contract_id_for_job(job_id)
            if not contract_id:
                logger.warning(f"No contract found for job {job_id}")
                return None
            
            # Return contract data
            return self.blockchain.contracts.get(contract_id)
            
        except Exception as e:
            logger.error(f"Get contract status failed: {e}")
            return None
