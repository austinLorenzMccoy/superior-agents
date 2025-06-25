# GigNova Manual Cloud Deployment Guide

This guide provides step-by-step instructions for manually deploying the GigNova platform to cloud services:
- Backend on Railway (Free Tier)
- Frontend on Netlify (Free Tier)
- Smart Contract on a public testnet

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Backend Manual Deployment on Railway](#backend-manual-deployment-on-railway)
3. [Frontend Manual Deployment on Netlify](#frontend-manual-deployment-on-netlify)
4. [Smart Contract Deployment on Testnet](#smart-contract-deployment-on-testnet)
5. [Connecting Components](#connecting-components)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

Before starting, make sure you have:

- **GitHub Account**: Your code is already in a repository
- **Railway Account**: Sign up at [railway.app](https://railway.app)
- **Netlify Account**: Sign up at [netlify.com](https://netlify.com)
- **MetaMask Wallet**: Install the [MetaMask browser extension](https://metamask.io/download/)
- **Alchemy Account**: Sign up at [alchemy.com](https://www.alchemy.com/) for testnet access
- **Test ETH**: Obtain from a faucet like [faucet.sepolia.dev](https://faucet.sepolia.dev)

## Backend Manual Deployment on Railway

### Step 1: Prepare Your Backend for Railway

1. Create a `Procfile` in your backend directory:
   ```bash
   cd /Users/a/Documents/Agrlab/superior-agents/GigNova/backend
   touch Procfile
   ```

2. Add the following content to the `Procfile`:
   ```
   web: cd backend && uvicorn gignova.app:app --host 0.0.0.0 --port $PORT
   ```

3. Create a `railway.json` file in your backend directory:
   ```bash
   touch railway.json
   ```

4. Add the following content to `railway.json`:
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "NIXPACKS",
       "buildCommand": "cd backend && pip install -r requirements.txt"
     },
     "deploy": {
       "startCommand": "cd backend && uvicorn gignova.app:app --host 0.0.0.0 --port $PORT",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

### Step 2: Deploy to Railway

1. Log in to your Railway account at [railway.app](https://railway.app)

2. Click on "New Project" and select "Deploy from GitHub repo"

3. Connect your GitHub account if you haven't already

4. Select your repository: `austinLorenzMccoy/superior-agents`

5. Configure the deployment settings:
   - **Root Directory**: `/GigNova`
   - **Environment**: Python

6. Add the following environment variables:
   - `PORT`: `8000`
   - `ENVIRONMENT`: `production`
   - `JWT_SECRET`: Generate a secure random string (e.g., use an online generator)
   - `DEV_MODE`: `false`

7. Click "Deploy"

### Step 3: Verify Backend Deployment

1. Wait for the deployment to complete (this may take a few minutes)
2. Once deployed, Railway will provide a URL for your service (e.g., `https://gignova-backend-production.up.railway.app`)
3. Test the health endpoint: `https://gignova-backend-production.up.railway.app/api/v1/health`
4. Note down your backend URL for later use

### Step 4: Monitor Usage

1. Railway's free tier provides $5 of usage credits per month
2. Monitor your usage in the Railway dashboard to ensure you stay within the free tier limits

## Frontend Manual Deployment on Netlify

### Step 1: Prepare Your Frontend

1. Create a production environment file in your local repository:

```bash
cd GigNova/frontend
echo "VITE_API_URL=https://your-backend-url.onrender.com/api/v1" > .env.production
```

2. Commit and push this change to GitHub

### Step 2: Deploy on Netlify

1. Log in to your Netlify account
2. Click "Add new site" and select "Import an existing project"
3. Connect to GitHub and select your repository: `austinLorenzMccoy/superior-agents`
4. Configure the build settings:
   - **Base directory**: `GigNova/frontend` (important since your project is in a subdirectory)
   - **Build command**: `npm run build`
   - **Publish directory**: `dist` (Netlify will automatically prepend the base directory)
5. Expand "Advanced build settings" and add environment variables:
   - `VITE_API_URL`: Your Render backend URL with `/api/v1` appended
6. Click "Deploy site"

### Step 3: Configure Custom Domain (Optional)

1. Go to "Domain settings" in your Netlify dashboard
2. Click "Add custom domain"
3. Follow the instructions to set up your domain

## Smart Contract Deployment on Testnet

### Step 1: Configure Hardhat for Testnet

1. Create a `.env` file in your `GigNova/contracts` directory:

```bash
cd GigNova/contracts
echo "ALCHEMY_API_KEY=your_alchemy_api_key" > .env
echo "PRIVATE_KEY=your_metamask_private_key" >> .env
```

2. Update your `hardhat.config.js` file:

```javascript
require("@nomicfoundation/hardhat-toolbox");
require('dotenv').config();

const ALCHEMY_API_KEY = process.env.ALCHEMY_API_KEY;
const PRIVATE_KEY = process.env.PRIVATE_KEY;

module.exports = {
  solidity: "0.8.19",
  networks: {
    sepolia: {
      url: `https://eth-sepolia.g.alchemy.com/v2/${ALCHEMY_API_KEY}`,
      accounts: [PRIVATE_KEY]
    }
  }
};
```

### Step 2: Get Testnet ETH

1. Open MetaMask and switch to the Sepolia testnet
2. Copy your wallet address
3. Go to [faucet.sepolia.dev](https://faucet.sepolia.dev) and request test ETH
4. Wait for the ETH to arrive in your wallet

### Step 3: Deploy the Contract

1. Deploy the contract to the Sepolia testnet:

```bash
cd GigNova/contracts
npx hardhat run scripts/deploy_gignova_contract.js --network sepolia
```

2. Note the contract address from the console output

### Step 4: Verify the Contract (Optional)

1. Add Etherscan API key to your `.env` file:

```bash
echo "ETHERSCAN_API_KEY=your_etherscan_api_key" >> .env
```

2. Update `hardhat.config.js` to include Etherscan:

```javascript
module.exports = {
  // ... existing config
  etherscan: {
    apiKey: process.env.ETHERSCAN_API_KEY
  }
};
```

3. Verify the contract:

```bash
npx hardhat verify --network sepolia DEPLOYED_CONTRACT_ADDRESS
```

## Connecting Components

### Step 1: Update Frontend with Contract Address

1. Go to your Netlify dashboard
2. Navigate to "Site settings" > "Environment variables"
3. Add a new environment variable:
   - `VITE_CONTRACT_ADDRESS`: Your deployed contract address
4. Trigger a new deployment: Go to "Deploys" and click "Trigger deploy"

### Step 2: Update Backend with Contract Address

1. Go to your Render dashboard
2. Navigate to your backend service
3. Go to "Environment" tab
4. Add a new environment variable:
   - `CONTRACT_ADDRESS`: Your deployed contract address
5. Click "Save Changes" and wait for the service to restart

### Step 3: Test the Complete Deployment

1. Open your Netlify site URL
2. Connect with MetaMask (make sure you're on Sepolia testnet)
3. Test the complete workflow:
   - Create a job
   - Submit a proposal
   - Accept a proposal
   - Complete a job
   - Submit a quality assessment

## Troubleshooting

### Backend Issues

- **Deployment Fails**: 
  - Check your repository structure to ensure Railway can find your code
  - Review the deployment logs in the Railway dashboard
  - Make sure all required dependencies are in your requirements.txt

- **API Not Responding**:
  - Check logs in the Railway dashboard
  - Verify your app is listening on the port specified by the `PORT` environment variable
  - Make sure your app hasn't exceeded the free tier usage limits

- **CORS Issues**:
  - Ensure your backend allows requests from your Netlify domain
  - Add your Netlify URL to the allowed origins in your CORS configuration

- **Free Tier Limitations**:
  - Railway provides $5 of free credits per month
  - Monitor your usage in the Railway dashboard
  - Consider setting up usage alerts

### Frontend Issues

- **Build Fails**:
  - Check Netlify build logs for errors
  - Verify that all dependencies are listed in package.json
  - Make sure your build command is correct

- **API Connection Errors**:
  - Check browser console for specific errors
  - Verify the `VITE_API_URL` is correct and includes the full path to your API
  - Test API endpoints directly using tools like Postman

- **Blank Screen**:
  - Check for JavaScript errors in the browser console
  - Verify that your frontend is correctly built and deployed

### Smart Contract Issues

- **Deployment Fails**:
  - Make sure you have enough test ETH for gas fees
  - Check that your private key is correctly set in the .env file
  - Verify network configuration in hardhat.config.js

- **Contract Interaction Errors**:
  - Ensure you're connected to the correct network in MetaMask
  - Check that the contract address is correctly set in your frontend
  - Verify that the ABI matches the deployed contract

### General Tips

1. Always check logs first when troubleshooting
2. Use browser developer tools to debug frontend issues
3. Test API endpoints with tools like Postman
4. For contract issues, use Etherscan to inspect transactions

---

Congratulations! You've successfully deployed the GigNova platform to cloud services. Your application is now accessible worldwide with a scalable backend on Render, a fast frontend on Netlify, and a smart contract on the Sepolia testnet.
