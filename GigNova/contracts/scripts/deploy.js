// We require the Hardhat Runtime Environment explicitly here. This is optional
// but useful for running the script in a standalone fashion through `node <script>`.
const hre = require("hardhat");

async function main() {
  // Hardhat always runs the compile task when running scripts with its command
  // line interface.
  //
  // If this script is run directly using `node` you may want to call compile
  // manually to make sure everything is compiled
  // await hre.run('compile');

  console.log("Deploying MetaGig contract...");

  // We get the contract to deploy
  const MetaGig = await hre.ethers.getContractFactory("MetaGig");
  const metaGig = await MetaGig.deploy();

  await metaGig.deployed();

  console.log("MetaGig deployed to:", metaGig.address);
  
  // Wait for a few confirmations for Etherscan verification
  console.log("Waiting for confirmations...");
  await metaGig.deployTransaction.wait(5);
  
  // Verify the contract on Etherscan if not on local network
  if (network.name !== "hardhat" && network.name !== "localhost") {
    console.log("Verifying contract on Etherscan...");
    try {
      await hre.run("verify:verify", {
        address: metaGig.address,
        constructorArguments: [],
      });
      console.log("Contract verified on Etherscan!");
    } catch (error) {
      console.error("Error verifying contract:", error);
    }
  }
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
