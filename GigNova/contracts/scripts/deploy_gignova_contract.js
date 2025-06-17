// Deployment script for GigNovaContract
const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying GigNovaContract...");
  
  // Deploy the contract
  const GigNovaContract = await ethers.getContractFactory("GigNovaContract");
  const gigNovaContract = await GigNovaContract.deploy();
  
  await gigNovaContract.deployed();
  
  console.log(`GigNovaContract deployed to: ${gigNovaContract.address}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
