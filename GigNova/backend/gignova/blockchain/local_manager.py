#!/usr/bin/env python3
"""
Local Blockchain Manager for GigNova
Provides a JSON file-based implementation for testing without an Ethereum node
"""

import logging
import asyncio
import os
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalBlockchainManager:
    """
    Local JSON file-based implementation of BlockchainManager for testing without an Ethereum node
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the local blockchain manager
        
        Args:
            data_dir: Directory to store blockchain data (defaults to ~/.gignova/blockchain)
        """
        if data_dir is None:
            home_dir = os.path.expanduser("~")
            data_dir = os.path.join(home_dir, ".gignova", "blockchain")
        
        self.data_dir = data_dir
        self.escrows_file = os.path.join(data_dir, "escrows.json")
        self.transactions_file = os.path.join(data_dir, "transactions.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        if not os.path.exists(self.escrows_file):
            with open(self.escrows_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.transactions_file):
            with open(self.transactions_file, 'w') as f:
                json.dump({}, f)
        
        logger.info(f"Local Blockchain Manager initialized at {data_dir}")
    
    async def connect(self) -> bool:
        """
        Check if data directory is accessible
        
        Returns:
            bool: True if data directory is accessible
        """
        try:
            # Ensure data directory exists and is writable
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir, exist_ok=True)
            
            # Test write access
            test_file = os.path.join(self.data_dir, ".test_write")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            
            logger.info("Local blockchain connection established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to local blockchain: {str(e)}")
            return False
    
    def _load_escrows(self) -> Dict[str, Any]:
        """
        Load escrows from file
        
        Returns:
            Dict: Escrows data
        """
        try:
            with open(self.escrows_file, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, FileNotFoundError):
            # Return empty dict if file is empty or doesn't exist
            return {}
    
    def _save_escrows(self, escrows: Dict[str, Any]) -> None:
        """
        Save escrows to file
        
        Args:
            escrows: Escrows data
        """
        with open(self.escrows_file, 'w') as f:
            json.dump(escrows, f, indent=2)
    
    def _load_transactions(self) -> Dict[str, Any]:
        """
        Load transactions from file
        
        Returns:
            Dict: Transactions data
        """
        try:
            with open(self.transactions_file, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, FileNotFoundError):
            # Return empty dict if file is empty or doesn't exist
            return {}
    
    def _save_transactions(self, transactions: Dict[str, Any]) -> None:
        """
        Save transactions to file
        
        Args:
            transactions: Transactions data
        """
        with open(self.transactions_file, 'w') as f:
            json.dump(transactions, f, indent=2)
    
    def _generate_address(self) -> str:
        """
        Generate a mock Ethereum address
        
        Returns:
            str: Ethereum-like address
        """
        return f"0x{uuid.uuid4().hex[:40]}"
    
    def _generate_tx_hash(self) -> str:
        """
        Generate a mock transaction hash
        
        Returns:
            str: Transaction hash
        """
        return f"0x{uuid.uuid4().hex}"
    
    async def create_escrow(self, 
                           client_id: str, 
                           freelancer_id: str, 
                           amount: float, 
                           deadline: int) -> Dict[str, Any]:
        """
        Create a local escrow contract
        
        Args:
            client_id: ID of the client
            freelancer_id: ID of the freelancer
            amount: Amount to be held in escrow
            deadline: Deadline in seconds
            
        Returns:
            Dict with contract address and transaction hash
        """
        try:
            # Load current escrows
            escrows = self._load_escrows()
            transactions = self._load_transactions()
            
            # Generate contract address and transaction hash
            contract_address = self._generate_address()
            tx_hash = self._generate_tx_hash()
            
            # Create escrow entry
            escrows[contract_address] = {
                "client_id": client_id,
                "freelancer_id": freelancer_id,
                "amount": amount,
                "deadline": deadline,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "tx_hash": tx_hash
            }
            
            # Create transaction entry
            transactions[tx_hash] = {
                "type": "create_escrow",
                "contract_address": contract_address,
                "timestamp": datetime.now().isoformat(),
                "status": "confirmed",
                "gas_used": 150000,
                "gas_price": 20000000000  # 20 Gwei
            }
            
            # Save changes
            self._save_escrows(escrows)
            self._save_transactions(transactions)
            
            logger.info(f"Local escrow created: {contract_address}")
            
            return {
                "success": True,
                "contract_address": contract_address,
                "transaction_hash": tx_hash
            }
        except Exception as e:
            logger.error(f"Failed to create escrow: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def release_payment(self, 
                             escrow_id: str, 
                             amount: Optional[float] = None) -> Dict[str, Any]:
        """
        Release payment from escrow
        
        Args:
            escrow_id: ID of the escrow contract
            amount: Amount to release (defaults to full amount)
            
        Returns:
            Dict with success status and transaction hash
        """
        try:
            # Load current escrows
            escrows = self._load_escrows()
            transactions = self._load_transactions()
            
            if escrow_id not in escrows:
                return {"success": False, "error": f"Escrow {escrow_id} not found"}
            
            escrow = escrows[escrow_id]
            
            if escrow["status"] != "active":
                return {"success": False, "error": f"Escrow {escrow_id} is not active"}
            
            # Generate transaction hash
            tx_hash = self._generate_tx_hash()
            
            # Update escrow status
            escrow["status"] = "released"
            escrow["released_at"] = datetime.now().isoformat()
            
            # Create transaction entry
            transactions[tx_hash] = {
                "type": "release_payment",
                "contract_address": escrow_id,
                "timestamp": datetime.now().isoformat(),
                "status": "confirmed",
                "gas_used": 100000,
                "gas_price": 20000000000  # 20 Gwei
            }
            
            # Save changes
            self._save_escrows(escrows)
            self._save_transactions(transactions)
            
            logger.info(f"Local payment released for escrow: {escrow_id}")
            
            return {
                "success": True,
                "message": "Payment released successfully",
                "transaction_hash": tx_hash
            }
        except Exception as e:
            logger.error(f"Failed to release payment: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction status
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Dict with transaction status
        """
        try:
            # Load transactions
            transactions = self._load_transactions()
            
            if tx_hash not in transactions:
                return {"success": False, "error": f"Transaction {tx_hash} not found"}
            
            transaction = transactions[tx_hash]
            
            return {
                "success": True,
                "status": transaction["status"],
                "gas_used": transaction["gas_used"],
                "timestamp": transaction["timestamp"]
            }
        except Exception as e:
            logger.error(f"Failed to get transaction status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_escrow_details(self, escrow_id: str) -> Dict[str, Any]:
        """
        Get escrow details
        
        Args:
            escrow_id: ID of the escrow contract
            
        Returns:
            Dict with escrow details
        """
        try:
            # Load escrows
            escrows = self._load_escrows()
            
            if escrow_id not in escrows:
                return {"success": False, "error": f"Escrow {escrow_id} not found"}
            
            escrow = escrows[escrow_id]
            
            return {
                "success": True,
                "escrow": escrow
            }
        except Exception as e:
            logger.error(f"Failed to get escrow details: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Create a singleton instance
local_blockchain_manager = LocalBlockchainManager()
