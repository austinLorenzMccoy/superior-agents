#!/bin/bash
# AutoTradeX Deployment Script
# This script helps deploy the AutoTradeX application to Render and Netlify

echo "🚀 AutoTradeX Deployment Script"
echo "==============================="

# Check if render-cli is installed
if ! command -v render &> /dev/null; then
    echo "❌ render-cli not found. Please install it first:"
    echo "npm install -g @render/cli"
    exit 1
fi

# Check if netlify-cli is installed
if ! command -v netlify &> /dev/null; then
    echo "❌ netlify-cli not found. Please install it first:"
    echo "npm install -g netlify-cli"
    exit 1
fi

# Function to deploy backend to Render
deploy_backend() {
    echo "📦 Deploying backend to Render..."
    
    # Deploy using render-cli and the render.yaml file
    render deploy --yaml render.yaml
    
    echo "✅ Backend deployment initiated. Check the Render dashboard for progress."
}

# Function to deploy frontend to Netlify
deploy_frontend() {
    echo "🌐 Deploying frontend to Netlify..."
    
    # Deploy using netlify-cli from the project root
    # This ensures Netlify can find the correct directory structure
    netlify deploy --prod
    
    echo "✅ Frontend deployment completed."
}

# Main deployment process
echo "Starting deployment process..."

# 1. Commit any pending changes
echo "Checking for uncommitted changes..."
if [[ -n $(git status --porcelain) ]]; then
    read -p "There are uncommitted changes. Do you want to commit them? (y/n): " commit_changes
    if [[ $commit_changes == "y" ]]; then
        read -p "Enter commit message: " commit_message
        git add .
        git commit -m "$commit_message"
    else
        echo "⚠️ Proceeding with deployment without committing changes."
    fi
fi

# 2. Push to GitHub
echo "Pushing latest changes to GitHub..."
git push origin main

# 3. Deploy backend and frontend
read -p "Deploy backend to Render? (y/n): " deploy_back
if [[ $deploy_back == "y" ]]; then
    deploy_backend
fi

read -p "Deploy frontend to Netlify? (y/n): " deploy_front
if [[ $deploy_front == "y" ]]; then
    deploy_frontend
fi

echo "🎉 Deployment process completed!"
echo "Backend URL: https://autotradex.onrender.com"
echo "Frontend URL: Check your Netlify dashboard for the URL"
