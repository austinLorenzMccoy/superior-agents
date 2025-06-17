# GigNova Smart Contracts

This directory contains the smart contracts for the GigNova freelancer platform, designed to align with the backend implementation.

## Overview

GigNova is a decentralized freelancer platform that connects clients and freelancers, providing secure escrow services through blockchain technology. The smart contracts in this repository handle job creation, payment escrow, dispute resolution, and payment release.

## Contract Structure

The main contract is `GigNovaContract.sol`, which implements the following features:

- Job creation with escrow funding
- Job completion tracking
- Payment release mechanism
- Dispute creation and resolution
- Platform fee management

## Job Status Flow

Jobs in GigNova follow this status flow:

1. **created** - Initial state when a job contract is created
2. **completed** - Job has been marked as completed by the client
3. **disputed** - (Optional) Job has a dispute that needs resolution
4. **paid** - Final state after payment has been released to the freelancer

## Directory Structure

```
contracts/
├── src/                    # Smart contract source files
│   └── GigNovaContract.sol # Main GigNova contract
├── scripts/                # Deployment and test scripts
│   ├── deploy_gignova_contract.js
│   └── test_gignova_contract.js
├── artifacts/              # Compiled contract artifacts (generated)
├── cache/                  # Hardhat cache
├── tests/                  # Contract test files
├── integration_guide.md    # Guide for integrating with backend
└── README.md               # This file
```

## Development Setup

### Prerequisites

- Node.js (v14+)
- npm or yarn

### Installation

```bash
# Install dependencies
npm install
```

### Environment Setup

Create a `.env` file based on `.env.example`:

```
PRIVATE_KEY=your_private_key
GOERLI_URL=your_goerli_rpc_url
SEPOLIA_URL=your_sepolia_rpc_url
MAINNET_URL=your_mainnet_rpc_url
```

## Usage

### Compiling Contracts

```bash
npx hardhat compile
```

### Running Tests

```bash
npx hardhat test
```

### Deploying Contracts

```bash
# Deploy to local network
npx hardhat run scripts/deploy_gignova_contract.js --network localhost

# Deploy to testnet
npx hardhat run scripts/deploy_gignova_contract.js --network goerli

# Deploy to mainnet
npx hardhat run scripts/deploy_gignova_contract.js --network mainnet
```

### Testing Contract Functionality

```bash
npx hardhat run scripts/test_gignova_contract.js --network localhost
```

## Integration with Backend

The smart contracts are designed to align with the backend's `LocalBlockchain` implementation. For detailed integration instructions, see [integration_guide.md](./integration_guide.md).

## Contract Functions

### GigNovaContract

- `createJob(string jobId, address freelancer, string ipfsHash) payable returns (string)` - Creates a new job contract
- `completeJob(string contractId)` - Marks a job as completed
- `releasePayment(string contractId)` - Releases payment to the freelancer
- `createDispute(string contractId)` - Creates a dispute for a job
- `resolveDispute(string contractId, uint16 clientShare)` - Resolves a dispute with specified fund distribution
- `getContract(string contractId) view returns (JobContract)` - Gets contract details by ID
- `getContractIdForJob(string jobId) view returns (string)` - Gets contract ID for a job

## Events

- `JobCreated(string contractId, string jobId, address client, address freelancer, uint256 amount)`
- `JobCompleted(string contractId, string jobId)`
- `PaymentReleased(string contractId, string jobId, uint256 amount)`
- `JobDisputed(string contractId, string jobId)`
- `FeePercentChanged(uint16 newFeePercent)`

## License

This project is licensed under the MIT License.
