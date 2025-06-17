// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title GigNovaContract
 * @dev Smart contract for the GigNova freelancer platform, aligned with backend implementation
 */
contract GigNovaContract is Ownable, ReentrancyGuard {
    // Fee percentage (in basis points, 100 = 1%)
    uint16 public platformFeePercent = 250; // 2.5% by default
    
    // Job status constants (matching backend implementation)
    string constant JOB_STATUS_CREATED = "created";
    string constant JOB_STATUS_COMPLETED = "completed";
    string constant JOB_STATUS_DISPUTED = "disputed";
    string constant JOB_STATUS_PAID = "paid";
    
    // Contract structure (matching backend implementation)
    struct JobContract {
        string jobId;
        address client;
        address freelancer;
        uint256 amount;
        string ipfsHash;
        string status;
        uint256 createdAt;
    }
    
    // Transaction structure
    struct Transaction {
        string transactionType;
        string contractId;
        string jobId;
        uint256 amount;
        uint256 timestamp;
    }
    
    // Mapping for contracts and transactions
    mapping(string => JobContract) public contracts;
    Transaction[] public transactions;
    
    // Events
    event JobCreated(string contractId, string jobId, address client, address freelancer, uint256 amount);
    event JobCompleted(string contractId, string jobId);
    event PaymentReleased(string contractId, string jobId, uint256 amount);
    event JobDisputed(string contractId, string jobId);
    event FeePercentChanged(uint16 newFeePercent);
    
    /**
     * @dev Constructor
     */
    constructor() Ownable() {}
    
    /**
     * @dev Generate a UUID v4-like identifier
     * @return A string representing a pseudo-UUID
     */
    function generateUUID() internal view returns (string memory) {
        bytes32 hash = keccak256(abi.encodePacked(
            block.timestamp,
            block.prevrandao,
            msg.sender,
            address(this)
        ));
        
        bytes memory uuid = new bytes(36);
        bytes memory alphabet = "0123456789abcdef";
        
        // Format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
        // Where y is 8, 9, a, or b
        
        for (uint i = 0; i < 36; i++) {
            if (i == 8 || i == 13 || i == 18 || i == 23) {
                uuid[i] = "-";
            } else if (i == 14) {
                uuid[i] = "4"; // Version 4
            } else if (i == 19) {
                // Use modulo of the first byte to avoid out-of-bounds access
                uuid[i] = alphabet[8 + (uint8(hash[0]) % 4)]; // 8, 9, a, or b
            } else {
                // Use a different byte from the hash for each position to avoid out-of-bounds
                uint8 hashByte = uint8(hash[i % 32]); // hash is 32 bytes long
                uuid[i] = alphabet[hashByte % 16];
            }
        }
        
        return string(uuid);
    }
    
    /**
     * @dev Create a new job contract
     * @param jobId Job ID from the backend
     * @param freelancer Address of the freelancer
     * @param ipfsHash IPFS hash containing job details
     * @return contractId The ID of the created contract
     */
    function createJob(
        string memory jobId,
        address freelancer,
        string memory ipfsHash
    ) external payable returns (string memory) {
        require(msg.value > 0, "Job amount must be greater than 0");
        
        // Generate a contract ID
        string memory contractId = generateUUID();
        
        // Create contract
        contracts[contractId] = JobContract({
            jobId: jobId,
            client: msg.sender,
            freelancer: freelancer,
            amount: msg.value,
            ipfsHash: ipfsHash,
            status: JOB_STATUS_CREATED,
            createdAt: block.timestamp
        });
        
        // Record transaction
        transactions.push(Transaction({
            transactionType: "create_job",
            contractId: contractId,
            jobId: jobId,
            amount: 0,
            timestamp: block.timestamp
        }));
        
        emit JobCreated(contractId, jobId, msg.sender, freelancer, msg.value);
        
        return contractId;
    }
    
    /**
     * @dev Mark a job as completed
     * @param contractId Contract ID
     */
    function completeJob(string memory contractId) external {
        JobContract storage jobContract = contracts[contractId];
        
        require(bytes(jobContract.jobId).length > 0, "Contract does not exist");
        require(keccak256(bytes(jobContract.status)) == keccak256(bytes(JOB_STATUS_CREATED)), "Job is not in created state");
        require(jobContract.client == msg.sender, "Only client can mark job as completed");
        
        // Update contract status
        jobContract.status = JOB_STATUS_COMPLETED;
        
        // Record transaction
        transactions.push(Transaction({
            transactionType: "complete_job",
            contractId: contractId,
            jobId: jobContract.jobId,
            amount: 0,
            timestamp: block.timestamp
        }));
        
        emit JobCompleted(contractId, jobContract.jobId);
    }
    
    /**
     * @dev Release payment for a job
     * @param contractId Contract ID
     */
    function releasePayment(string memory contractId) external nonReentrant {
        JobContract storage jobContract = contracts[contractId];
        
        require(bytes(jobContract.jobId).length > 0, "Contract does not exist");
        require(keccak256(bytes(jobContract.status)) == keccak256(bytes(JOB_STATUS_COMPLETED)), "Job must be completed first");
        require(jobContract.client == msg.sender, "Only client can release payment");
        
        // Update contract status
        jobContract.status = JOB_STATUS_PAID;
        
        // Calculate fee and payment
        uint256 fee = (jobContract.amount * platformFeePercent) / 10000;
        uint256 payment = jobContract.amount - fee;
        
        // Record transaction
        transactions.push(Transaction({
            transactionType: "release_payment",
            contractId: contractId,
            jobId: jobContract.jobId,
            amount: jobContract.amount,
            timestamp: block.timestamp
        }));
        
        // Transfer payment to freelancer
        (bool sentToFreelancer, ) = payable(jobContract.freelancer).call{value: payment}("");
        require(sentToFreelancer, "Failed to send payment to freelancer");
        
        // Transfer fee to contract owner
        (bool sentToOwner, ) = payable(owner()).call{value: fee}("");
        require(sentToOwner, "Failed to send fee to owner");
        
        emit PaymentReleased(contractId, jobContract.jobId, jobContract.amount);
    }
    
    /**
     * @dev Create a dispute for a job
     * @param contractId Contract ID
     */
    function createDispute(string memory contractId) external {
        JobContract storage jobContract = contracts[contractId];
        
        require(bytes(jobContract.jobId).length > 0, "Contract does not exist");
        require(
            keccak256(bytes(jobContract.status)) == keccak256(bytes(JOB_STATUS_CREATED)) || 
            keccak256(bytes(jobContract.status)) == keccak256(bytes(JOB_STATUS_COMPLETED)),
            "Job must be in created or completed state"
        );
        require(
            jobContract.client == msg.sender || jobContract.freelancer == msg.sender,
            "Only client or freelancer can create a dispute"
        );
        
        // Update contract status
        jobContract.status = JOB_STATUS_DISPUTED;
        
        // Record transaction
        transactions.push(Transaction({
            transactionType: "create_dispute",
            contractId: contractId,
            jobId: jobContract.jobId,
            amount: 0,
            timestamp: block.timestamp
        }));
        
        emit JobDisputed(contractId, jobContract.jobId);
    }
    
    /**
     * @dev Resolve a dispute (only owner can do this)
     * @param contractId Contract ID
     * @param clientShare Percentage of funds to return to client (in basis points, 10000 = 100%)
     */
    function resolveDispute(string memory contractId, uint16 clientShare) external onlyOwner nonReentrant {
        JobContract storage jobContract = contracts[contractId];
        
        require(bytes(jobContract.jobId).length > 0, "Contract does not exist");
        require(keccak256(bytes(jobContract.status)) == keccak256(bytes(JOB_STATUS_DISPUTED)), "Job is not disputed");
        require(clientShare <= 10000, "Client share cannot exceed 100%");
        
        // Calculate shares
        uint256 clientAmount = (jobContract.amount * clientShare) / 10000;
        uint256 freelancerAmount = jobContract.amount - clientAmount;
        
        // Update contract status
        jobContract.status = JOB_STATUS_PAID;
        
        // Record transaction
        transactions.push(Transaction({
            transactionType: "resolve_dispute",
            contractId: contractId,
            jobId: jobContract.jobId,
            amount: jobContract.amount,
            timestamp: block.timestamp
        }));
        
        // Transfer client share
        if (clientAmount > 0) {
            (bool sentToClient, ) = payable(jobContract.client).call{value: clientAmount}("");
            require(sentToClient, "Failed to send funds to client");
        }
        
        // Transfer freelancer share
        if (freelancerAmount > 0) {
            (bool sentToFreelancer, ) = payable(jobContract.freelancer).call{value: freelancerAmount}("");
            require(sentToFreelancer, "Failed to send funds to freelancer");
        }
    }
    
    /**
     * @dev Set the platform fee percentage
     * @param _feePercent New fee percentage (in basis points, 100 = 1%)
     */
    function setPlatformFeePercent(uint16 _feePercent) external onlyOwner {
        require(_feePercent <= 1000, "Fee cannot exceed 10%");
        platformFeePercent = _feePercent;
        emit FeePercentChanged(_feePercent);
    }
    
    /**
     * @dev Get contract by ID
     * @param contractId Contract ID
     * @return JobContract details
     */
    function getContract(string memory contractId) external view returns (JobContract memory) {
        return contracts[contractId];
    }
    
    /**
     * @dev Get contract by job ID
     * @param jobId Job ID
     * @return contractId Contract ID
     */
    function getContractIdForJob(string memory jobId) external view returns (string memory) {
        for (uint i = 0; i < transactions.length; i++) {
            if (keccak256(bytes(transactions[i].jobId)) == keccak256(bytes(jobId)) &&
                keccak256(bytes(transactions[i].transactionType)) == keccak256(bytes("create_job"))) {
                return transactions[i].contractId;
            }
        }
        return "";
    }
}
