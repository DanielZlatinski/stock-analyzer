#!/bin/bash

# Firebase Deployment Script
# This script helps deploy your Flask app to Firebase Hosting with Cloud Run backend

set -e

echo "🚀 Starting Firebase deployment..."

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo "❌ Firebase CLI not found. Please install it:"
    echo "   npm install -g firebase-tools"
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK not found. Please install it:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID from .firebaserc
PROJECT_ID=$(grep -o '"default": "[^"]*"' .firebaserc | cut -d'"' -f4)

if [ "$PROJECT_ID" == "your-firebase-project-id" ] || [ -z "$PROJECT_ID" ]; then
    echo "❌ Please update .firebaserc with your Firebase project ID"
    exit 1
fi

echo "📦 Project ID: $PROJECT_ID"

# Set gcloud project
echo "🔧 Setting Google Cloud project..."
gcloud config set project $PROJECT_ID

# Deploy to Cloud Run
echo "🐳 Deploying backend to Cloud Run..."
gcloud run deploy stock-analyzer \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars FINNHUB_API_KEY=d5l1bthr01qt47mg4io0d5l1bthr01qt47mg4iog,LOW_MEMORY_MODE=1 \
  --quiet

echo "✅ Backend deployed successfully!"

# Deploy to Firebase Hosting
echo "🔥 Deploying frontend to Firebase Hosting..."
firebase deploy --only hosting

echo "✅ Deployment complete!"
echo ""
echo "🌐 Your app should be live at: https://$PROJECT_ID.web.app"
echo "📊 Cloud Run service: https://console.cloud.google.com/run/detail/us-central1/stock-analyzer"
