// Test script for GigNovaContract
const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying GigNovaContract for testing...");
  
  // Deploy the contract
  const GigNovaContract = await ethers.getContractFactory("GigNovaContract");
  const gigNovaContract = await GigNovaContract.deploy();
  await gigNovaContract.deployed();
  
  console.log(`GigNovaContract deployed to: ${gigNovaContract.address}`);
  
  // Get signers for testing
  const [owner, client, freelancer] = await ethers.getSigners();
  
  console.log("Test accounts:");
  console.log(`Owner: ${owner.address}`);
  console.log(`Client: ${client.address}`);
  console.log(`Freelancer: ${freelancer.address}`);
  
  // Test job creation
  console.log("\nCreating a new job...");
  const jobId = "job-123";
  const ipfsHash = "QmT78zSuBmuS4z925WZfrqQ1qHaJ56DQaTfyMUF7F8ff5o";
  const jobAmount = ethers.utils.parseEther("1.0"); // 1 ETH
  
  const createTx = await gigNovaContract.connect(client).createJob(
    jobId,
    freelancer.address,
    ipfsHash,
    { value: jobAmount }
  );
  
  const createReceipt = await createTx.wait();
  const createEvent = createReceipt.events.find(event => event.event === 'JobCreated');
  const contractId = createEvent.args.contractId;
  
  console.log(`Job created with contract ID: ${contractId}`);
  
  // Get contract details
  const contractDetails = await gigNovaContract.getContract(contractId);
  console.log("\nContract details:");
  console.log(`Job ID: ${contractDetails.jobId}`);
  console.log(`Client: ${contractDetails.client}`);
  console.log(`Freelancer: ${contractDetails.freelancer}`);
  console.log(`Amount: ${ethers.utils.formatEther(contractDetails.amount)} ETH`);
  console.log(`Status: ${contractDetails.status}`);
  
  // Mark job as completed
  console.log("\nMarking job as completed...");
  const completeTx = await gigNovaContract.connect(client).completeJob(contractId);
  await completeTx.wait();
  
  // Get updated contract details
  const updatedContractDetails = await gigNovaContract.getContract(contractId);
  console.log(`Job status updated to: ${updatedContractDetails.status}`);
  
  // Release payment
  console.log("\nReleasing payment...");
  const releaseTx = await gigNovaContract.connect(client).releasePayment(contractId);
  await releaseTx.wait();
  
  // Get final contract details
  const finalContractDetails = await gigNovaContract.getContract(contractId);
  console.log(`Job status updated to: ${finalContractDetails.status}`);
  
  // Test dispute flow with a new job
  console.log("\n--- Testing dispute flow ---");
  const disputeJobId = "job-456";
  const disputeCreateTx = await gigNovaContract.connect(client).createJob(
    disputeJobId,
    freelancer.address,
    ipfsHash,
    { value: jobAmount }
  );
  
  const disputeCreateReceipt = await disputeCreateTx.wait();
  const disputeCreateEvent = disputeCreateReceipt.events.find(event => event.event === 'JobCreated');
  const disputeContractId = disputeCreateEvent.args.contractId;
  
  console.log(`Dispute test job created with contract ID: ${disputeContractId}`);
  
  // Create dispute
  console.log("\nCreating a dispute...");
  const disputeTx = await gigNovaContract.connect(freelancer).createDispute(disputeContractId);
  await disputeTx.wait();
  
  // Get dispute contract details
  const disputeContractDetails = await gigNovaContract.getContract(disputeContractId);
  console.log(`Job status updated to: ${disputeContractDetails.status}`);
  
  // Resolve dispute (50/50 split)
  console.log("\nResolving dispute (50/50 split)...");
  const resolveTx = await gigNovaContract.connect(owner).resolveDispute(disputeContractId, 5000);
  await resolveTx.wait();
  
  // Get final dispute contract details
  const finalDisputeContractDetails = await gigNovaContract.getContract(disputeContractId);
  console.log(`Job status updated to: ${finalDisputeContractDetails.status}`);
  
  console.log("\nTest completed successfully!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
