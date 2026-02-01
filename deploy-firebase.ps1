# Firebase Deployment Script for PowerShell
# This script helps deploy your Flask app to Firebase Hosting with Cloud Run backend

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Firebase deployment..." -ForegroundColor Cyan

# Check if Firebase CLI is installed
try {
    $null = Get-Command firebase -ErrorAction Stop
} catch {
    Write-Host "❌ Firebase CLI not found. Please install it:" -ForegroundColor Red
    Write-Host "   npm install -g firebase-tools" -ForegroundColor Yellow
    exit 1
}

# Check if gcloud is installed
try {
    $null = Get-Command gcloud -ErrorAction Stop
} catch {
    Write-Host "❌ Google Cloud SDK not found. Please install it:" -ForegroundColor Red
    Write-Host "   https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Get project ID from .firebaserc
$firebasercContent = Get-Content .firebaserc -Raw
if ($firebasercContent -match '"default":\s*"([^"]+)"') {
    $PROJECT_ID = $matches[1]
} else {
    Write-Host "❌ Could not find project ID in .firebaserc" -ForegroundColor Red
    exit 1
}

if ($PROJECT_ID -eq "your-firebase-project-id" -or [string]::IsNullOrEmpty($PROJECT_ID)) {
    Write-Host "❌ Please update .firebaserc with your Firebase project ID" -ForegroundColor Red
    exit 1
}

Write-Host "📦 Project ID: $PROJECT_ID" -ForegroundColor Green

# Set gcloud project
Write-Host "🔧 Setting Google Cloud project..." -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

# Deploy to Cloud Run
Write-Host "🐳 Deploying backend to Cloud Run..." -ForegroundColor Cyan
gcloud run deploy stock-analyzer `
  --source . `
  --region us-central1 `
  --platform managed `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1 `
  --timeout 300 `
  --max-instances 10 `
  --set-env-vars FINNHUB_API_KEY=d5l1bthr01qt47mg4io0d5l1bthr01qt47mg4iog,LOW_MEMORY_MODE=1 `
  --quiet

Write-Host "✅ Backend deployed successfully!" -ForegroundColor Green

# Deploy to Firebase Hosting
Write-Host "🔥 Deploying frontend to Firebase Hosting..." -ForegroundColor Cyan
firebase deploy --only hosting

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Your app should be live at: https://$PROJECT_ID.web.app" -ForegroundColor Cyan
Write-Host "📊 Cloud Run service: https://console.cloud.google.com/run/detail/us-central1/stock-analyzer" -ForegroundColor Cyan
