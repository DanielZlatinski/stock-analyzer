# Firebase Deployment Guide

This guide will help you deploy your Flask application to Firebase Hosting with Cloud Run backend.

## Prerequisites

1. **Install Firebase CLI:**
   ```bash
   npm install -g firebase-tools
   ```

2. **Install Google Cloud SDK:**
   - Download from: https://cloud.google.com/sdk/docs/install
   - Or use: `gcloud components install beta`

3. **Login to Firebase:**
   ```bash
   firebase login
   ```

4. **Login to Google Cloud:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" or select existing project
3. Enable Firebase Hosting
4. Copy your project ID

## Step 2: Update Firebase Configuration

1. Open `.firebaserc` and replace `your-firebase-project-id` with your actual Firebase project ID:
   ```json
   {
     "projects": {
       "default": "your-actual-project-id"
     }
   }
   ```

2. Make sure your Google Cloud project ID matches your Firebase project ID (they're the same)

## Step 3: Enable Required APIs

Enable the following APIs in Google Cloud Console:
- Cloud Run API
- Cloud Build API
- Container Registry API (or Artifact Registry API)

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## Step 4: Deploy Backend to Cloud Run

### Option A: Using Cloud Build (Recommended)

```bash
# Submit build to Cloud Build
gcloud builds submit --config cloudbuild.yaml

# Or deploy directly
gcloud run deploy stock-analyzer \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars FINNHUB_API_KEY=d5l1bthr01qt47mg4io0d5l1bthr01qt47mg4iog,LOW_MEMORY_MODE=1
```

### Option B: Using Docker

```bash
# Build the image
docker build -t gcr.io/YOUR_PROJECT_ID/stock-analyzer .

# Push to Container Registry
docker push gcr.io/YOUR_PROJECT_ID/stock-analyzer

# Deploy to Cloud Run
gcloud run deploy stock-analyzer \
  --image gcr.io/YOUR_PROJECT_ID/stock-analyzer \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars FINNHUB_API_KEY=d5l1bthr01qt47mg4io0d5l1bthr01qt47mg4iog,LOW_MEMORY_MODE=1
```

After deployment, note the Cloud Run service URL (e.g., `https://stock-analyzer-xxxxx-uc.a.run.app`)

## Step 5: Update Firebase Configuration

Update `firebase.json` to use your Cloud Run service URL. The current configuration uses the service name, but you may need to update it:

```json
{
  "hosting": {
    "rewrites": [
      {
        "source": "**",
        "run": {
          "serviceId": "stock-analyzer",
          "region": "us-central1"
        }
      }
    ]
  }
}
```

## Step 6: Deploy to Firebase Hosting

```bash
firebase deploy --only hosting
```

## Step 7: Verify Deployment

1. Visit your Firebase Hosting URL (shown after deployment)
2. Test the application functionality
3. Check Cloud Run logs if there are issues:
   ```bash
   gcloud run services logs read stock-analyzer --region us-central1
   ```

## Updating Your Deployment

### Update Backend:
```bash
gcloud run deploy stock-analyzer --source . --region us-central1
```

### Update Frontend:
```bash
firebase deploy --only hosting
```

### Update Both:
```bash
# Deploy backend first
gcloud run deploy stock-analyzer --source . --region us-central1

# Then deploy frontend
firebase deploy --only hosting
```

## Environment Variables

To update environment variables:
```bash
gcloud run services update stock-analyzer \
  --region us-central1 \
  --update-env-vars KEY=VALUE
```

## Troubleshooting

1. **Cloud Run service not found:**
   - Make sure you deployed to Cloud Run first
   - Verify the service name matches in `firebase.json`

2. **403 Forbidden errors:**
   - Ensure Cloud Run service allows unauthenticated access
   - Check IAM permissions

3. **Timeout errors:**
   - Increase timeout in Cloud Run settings
   - Check application logs for slow operations

4. **Build failures:**
   - Check `requirements.txt` for all dependencies
   - Verify Dockerfile is correct
   - Check Cloud Build logs

## Cost Considerations

- Firebase Hosting: Free tier includes 10 GB storage, 360 MB/day transfer
- Cloud Run: Pay per use, first 2 million requests/month free
- Cloud Build: 120 build-minutes/day free

## Additional Resources

- [Firebase Hosting Docs](https://firebase.google.com/docs/hosting)
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [Firebase + Cloud Run Integration](https://firebase.google.com/docs/hosting/cloud-run)
