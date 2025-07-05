#!/bin/bash
# AutoTradeX Deployment Script
echo "🚀 AutoTradeX Deployment Script"
echo "==============================="

# Parse command line arguments
DEPLOY_BACKEND=false
DEPLOY_FRONTEND=false

# If no arguments, deploy both
if [ $# -eq 0 ]; then
    DEPLOY_FRONTEND=true
    # Only try to deploy backend if render CLI is available
    if command -v render &> /dev/null; then
        DEPLOY_BACKEND=true
    else
        echo "⚠️ render-cli not found. Only deploying frontend."
        echo "To deploy backend, install render-cli: npm install -g @render/cli"
    fi
fi

# Process arguments
while [ $# -gt 0 ]; do
    case "$1" in
        --frontend)
            DEPLOY_FRONTEND=true
            ;;
        --backend)
            if ! command -v render &> /dev/null; then
                echo "❌ render-cli not found. Please install it first:"
                echo "npm install -g @render/cli"
                exit 1
            fi
            DEPLOY_BACKEND=true
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--frontend] [--backend]"
            exit 1
            ;;
    esac
    shift
done

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
if [[ $DEPLOY_BACKEND == true ]]; then
    deploy_backend
fi

if [[ $DEPLOY_FRONTEND == true ]]; then
    deploy_frontend
fi

echo "🎉 Deployment process completed!"
echo "Backend URL: https://autotradex.onrender.com"
echo "Frontend URL: Check your Netlify dashboard for the URL"
