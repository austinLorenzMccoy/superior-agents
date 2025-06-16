#!/usr/bin/env python3
"""
GigNova Blockchain Manager Tutorial

This script demonstrates how to use the blockchain manager component
of GigNova to create contracts, execute payments, and query transaction history.
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add the project root to the path so we can import the gignova package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from gignova.blockchain.manager import BlockchainManager
except ImportError:
    print("Error: Could not import BlockchainManager. Make sure you've installed the package.")
    sys.exit(1)

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80 + "\n")

def print_json(data):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2))
    print("-"*40)

def main():
    print_section("GigNova Blockchain Manager Tutorial")
    
    # Initialize the blockchain manager
    print("Initializing BlockchainManager...")
    blockchain = BlockchainManager()
    
    # Create user wallets
    print_section("1. Creating User Wallets")
    client_wallet = blockchain.create_wallet(user_id="client_123")
    freelancer_wallet = blockchain.create_wallet(user_id="freelancer_456")
    
    print("Client Wallet:")
    print_json(client_wallet.__dict__)
    
    print("Freelancer Wallet:")
    print_json(freelancer_wallet.__dict__)
    
    # Fund client wallet (in a real system, this would be through a payment processor)
    print_section("2. Funding Client Wallet")
    blockchain.fund_wallet(client_wallet.address, 1000)
    
    print("Client wallet balance:")
    balance = blockchain.get_wallet_balance(client_wallet.address)
    print(f"${balance}")
    
    # Create a smart contract
    print_section("3. Creating a Smart Contract")
    deadline = datetime.now() + timedelta(days=14)
    contract = blockchain.create_contract(
        client_id="client_123",
        freelancer_id="freelancer_456",
        job_id="job_789",
        payment_amount=500,
        deadline=deadline.isoformat()
    )
    
    print("Smart Contract Created:")
    print_json(contract.__dict__)
    
    # Check contract status
    print_section("4. Checking Contract Status")
    contract_status = blockchain.get_contract_status(contract.id)
    print(f"Contract Status: {contract_status}")
    
    # Escrow funds
    print_section("5. Placing Funds in Escrow")
    escrow_tx = blockchain.escrow_payment(
        contract_id=contract.id,
        amount=500,
        from_address=client_wallet.address
    )
    
    print("Escrow Transaction:")
    print_json(escrow_tx.__dict__)
    
    print("Client wallet balance after escrow:")
    balance = blockchain.get_wallet_balance(client_wallet.address)
    print(f"${balance}")
    
    # Execute payment (after work is completed and approved)
    print_section("6. Releasing Payment to Freelancer")
    payment_tx = blockchain.execute_payment(
        contract_id=contract.id,
        amount=500,
        from_address=client_wallet.address,
        to_address=freelancer_wallet.address
    )
    
    print("Payment Transaction:")
    print_json(payment_tx.__dict__)
    
    print("Freelancer wallet balance after payment:")
    balance = blockchain.get_wallet_balance(freelancer_wallet.address)
    print(f"${balance}")
    
    # Query transaction history
    print_section("7. Querying Transaction History")
    client_transactions = blockchain.get_transaction_history(client_wallet.address)
    
    print("Client Transaction History:")
    for tx in client_transactions:
        print(f"- {tx.timestamp}: {tx.transaction_type} ${tx.amount}")
    
    freelancer_transactions = blockchain.get_transaction_history(freelancer_wallet.address)
    
    print("\nFreelancer Transaction History:")
    for tx in freelancer_transactions:
        print(f"- {tx.timestamp}: {tx.transaction_type} ${tx.amount}")
    
    # Contract completion
    print_section("8. Completing the Contract")
    completed_contract = blockchain.complete_contract(contract.id)
    
    print("Completed Contract:")
    print_json(completed_contract.__dict__)
    
    print_section("Tutorial Complete!")
    print("""
This tutorial demonstrated the basic workflow of the GigNova blockchain system:
1. Creating user wallets
2. Funding a wallet
3. Creating a smart contract
4. Placing funds in escrow
5. Releasing payment upon work completion
6. Querying transaction history
7. Completing a contract

In a real application, these steps would be triggered by API calls and
integrated with the rest of the GigNova platform.
    """)

if __name__ == "__main__":
    main()
