const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("GigNovaContract", function () {
  let gigNovaContract;
  let owner;
  let client;
  let freelancer;
  let addr3;
  
  const oneEther = ethers.utils.parseEther("1.0");
  const halfEther = ethers.utils.parseEther("0.5");
  const ipfsHash = "QmT78zSuBmuS4z925WZfrqQ1qHaJ56DQaTfyMUF7F8ff5o";
  
  beforeEach(async function () {
    // Get signers
    [owner, client, freelancer, addr3] = await ethers.getSigners();
    
    // Deploy contract
    const GigNovaContract = await ethers.getContractFactory("GigNovaContract");
    gigNovaContract = await GigNovaContract.deploy();
    await gigNovaContract.deployed();
  });

  describe("Job Creation", function () {
    it("Should create a job successfully", async function () {
      const jobId = "job-123";
      
      const tx = await gigNovaContract.connect(client).createJob(
        jobId,
        freelancer.address,
        ipfsHash,
        { value: oneEther }
      );
      
      const receipt = await tx.wait();
      const event = receipt.events.find(e => e.event === 'JobCreated');
      expect(event).to.not.be.undefined;
      
      const contractId = event.args.contractId;
      expect(contractId).to.not.be.empty;
      
      const jobContract = await gigNovaContract.getContract(contractId);
      expect(jobContract.jobId).to.equal(jobId);
      expect(jobContract.client).to.equal(client.address);
      expect(jobContract.freelancer).to.equal(freelancer.address);
      expect(jobContract.amount).to.equal(oneEther);
      expect(jobContract.ipfsHash).to.equal(ipfsHash);
      expect(jobContract.status).to.equal("created");
    });
    
    it("Should fail if funding is zero", async function () {
      const jobId = "job-123";
      
      await expect(
        gigNovaContract.connect(client).createJob(
          jobId,
          freelancer.address,
          ipfsHash,
          { value: 0 }
        )
      ).to.be.revertedWith("Job amount must be greater than 0");
    });
  });
  
  describe("Job Completion", function () {
    let contractId;
    
    beforeEach(async function () {
      const jobId = "job-123";
      
      const tx = await gigNovaContract.connect(client).createJob(
        jobId,
        freelancer.address,
        ipfsHash,
        { value: oneEther }
      );
      
      const receipt = await tx.wait();
      const event = receipt.events.find(e => e.event === 'JobCreated');
      contractId = event.args.contractId;
    });
    
    it("Should mark a job as completed", async function () {
      await gigNovaContract.connect(client).completeJob(contractId);
      
      const jobContract = await gigNovaContract.getContract(contractId);
      expect(jobContract.status).to.equal("completed");
    });
    
    it("Should fail if non-client tries to complete job", async function () {
      await expect(
        gigNovaContract.connect(freelancer).completeJob(contractId)
      ).to.be.revertedWith("Only client can mark job as completed");
    });
  });
  
  describe("Payment Release", function () {
    let contractId;
    
    beforeEach(async function () {
      const jobId = "job-123";
      
      const tx = await gigNovaContract.connect(client).createJob(
        jobId,
        freelancer.address,
        ipfsHash,
        { value: oneEther }
      );
      
      const receipt = await tx.wait();
      const event = receipt.events.find(e => e.event === 'JobCreated');
      contractId = event.args.contractId;
      
      await gigNovaContract.connect(client).completeJob(contractId);
    });
    
    it("Should release payment successfully", async function () {
      const freelancerBalanceBefore = await ethers.provider.getBalance(freelancer.address);
      
      await gigNovaContract.connect(client).releasePayment(contractId);
      
      const jobContract = await gigNovaContract.getContract(contractId);
      expect(jobContract.status).to.equal("paid");
      
      const freelancerBalanceAfter = await ethers.provider.getBalance(freelancer.address);
      
      // Calculate expected payment (97.5% of oneEther)
      const expectedPayment = oneEther.mul(9750).div(10000);
      
      // Check that freelancer received payment (with some tolerance for gas costs)
      expect(freelancerBalanceAfter.sub(freelancerBalanceBefore)).to.be.closeTo(
        expectedPayment,
        ethers.utils.parseEther("0.01")
      );
    });
    
    it("Should fail if job is not completed", async function () {
      // Create a new job
      const jobId = "job-456";
      
      const tx = await gigNovaContract.connect(client).createJob(
        jobId,
        freelancer.address,
        ipfsHash,
        { value: oneEther }
      );
      
      const receipt = await tx.wait();
      const event = receipt.events.find(e => e.event === 'JobCreated');
      const newContractId = event.args.contractId;
      
      await expect(
        gigNovaContract.connect(client).releasePayment(newContractId)
      ).to.be.revertedWith("Job must be completed first");
    });
  });
  
  describe("Dispute Resolution", function () {
    let contractId;
    
    beforeEach(async function () {
      const jobId = "job-123";
      
      const tx = await gigNovaContract.connect(client).createJob(
        jobId,
        freelancer.address,
        ipfsHash,
        { value: oneEther }
      );
      
      const receipt = await tx.wait();
      const event = receipt.events.find(e => e.event === 'JobCreated');
      contractId = event.args.contractId;
    });
    
    it("Should create a dispute", async function () {
      await gigNovaContract.connect(freelancer).createDispute(contractId);
      
      const jobContract = await gigNovaContract.getContract(contractId);
      expect(jobContract.status).to.equal("disputed");
    });
    
    it("Should resolve a dispute", async function () {
      await gigNovaContract.connect(freelancer).createDispute(contractId);
      
      const clientBalanceBefore = await ethers.provider.getBalance(client.address);
      const freelancerBalanceBefore = await ethers.provider.getBalance(freelancer.address);
      
      // Resolve with 50/50 split
      await gigNovaContract.connect(owner).resolveDispute(contractId, 5000);
      
      const jobContract = await gigNovaContract.getContract(contractId);
      expect(jobContract.status).to.equal("paid");
      
      const clientBalanceAfter = await ethers.provider.getBalance(client.address);
      const freelancerBalanceAfter = await ethers.provider.getBalance(freelancer.address);
      
      // Client should get 50% of funds
      expect(clientBalanceAfter.sub(clientBalanceBefore)).to.be.closeTo(
        oneEther.div(2),
        ethers.utils.parseEther("0.01")
      );
      
      // Freelancer should get 50% of funds
      expect(freelancerBalanceAfter.sub(freelancerBalanceBefore)).to.be.closeTo(
        oneEther.div(2),
        ethers.utils.parseEther("0.01")
      );
    });
  });
  
  describe("Platform Fee", function () {
    it("Should set platform fee percentage", async function () {
      await gigNovaContract.connect(owner).setPlatformFeePercent(300);
      expect(await gigNovaContract.platformFeePercent()).to.equal(300);
    });
    
    it("Should fail if non-owner tries to set fee", async function () {
      await expect(
        gigNovaContract.connect(client).setPlatformFeePercent(300)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
    
    it("Should fail if fee exceeds maximum", async function () {
      await expect(
        gigNovaContract.connect(owner).setPlatformFeePercent(1100)
      ).to.be.revertedWith("Fee cannot exceed 10%");
    });
  });
});
