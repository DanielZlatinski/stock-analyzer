# Firebase Deployment - Step by Step Guide

Follow these steps in order to deploy your website to Firebase.

## Prerequisites Checklist

Before starting, make sure you have:
- [ ] A Google account
- [ ] A computer with internet connection
- [ ] Command line access (PowerShell on Windows, Terminal on Mac/Linux)

---

## STEP 1: Install Firebase CLI

### On Windows (PowerShell):
```powershell
npm install -g firebase-tools
```

### On Mac/Linux:
```bash
npm install -g firebase-tools
```

**Note:** If you don't have Node.js/npm installed:
- Download Node.js from: https://nodejs.org/
- Install it, then run the command above

**Verify installation:**
```bash
firebase --version
```
You should see a version number (e.g., `13.0.0`)

---

## STEP 2: Install Google Cloud SDK

### On Windows:
1. Download from: https://cloud.google.com/sdk/docs/install
2. Run the installer
3. Follow the installation wizard

### On Mac:
```bash
brew install --cask google-cloud-sdk
```

### On Linux:
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Verify installation:**
```bash
gcloud --version
```
You should see version information.

---

## STEP 3: Create Firebase Project

1. Go to: https://console.firebase.google.com/
2. Click **"Add project"** (or **"Create a project"**)
3. Enter a project name (e.g., "stock-analyzer")
4. Click **"Continue"**
5. **Disable** Google Analytics (optional, you can enable later)
6. Click **"Create project"**
7. Wait for project creation (takes ~30 seconds)
8. Click **"Continue"**

**Important:** Note your **Project ID** (shown in the project settings)

---

## STEP 4: Enable Firebase Hosting

1. In Firebase Console, click **"Hosting"** in the left menu
2. Click **"Get started"**
3. Follow the setup wizard (you can skip the initial deployment)
4. Click **"Continue to console"**

---

## STEP 5: Link Firebase Project to Your Code

1. Open PowerShell/Terminal in your project folder (`c:\Users\Daniel\ai_project`)
2. Login to Firebase:
   ```bash
   firebase login
   ```
3. A browser window will open - click **"Allow"** to authorize
4. Initialize Firebase in your project:
   ```bash
   firebase init hosting
   ```
5. When prompted:
   - **"Use an existing project"** → Select your project
   - **"What do you want to use as your public directory?"** → Type: `static`
   - **"Configure as a single-page app?"** → Type: `N` (No)
   - **"Set up automatic builds and deploys with GitHub?"** → Type: `N` (No)
   - **"File static/index.html already exists. Overwrite?"** → Type: `N` (No)

---

## STEP 6: Update Firebase Configuration

1. Open `.firebaserc` file in your project
2. Replace `your-firebase-project-id` with your actual project ID
3. Save the file

**Example:**
```json
{
  "projects": {
    "default": "stock-analyzer-12345"
  }
}
```

---

## STEP 7: Enable Google Cloud APIs

1. Go to: https://console.cloud.google.com/
2. Make sure you're in the same project (same project ID as Firebase)
3. Enable these APIs (search for each and click "Enable"):
   - **Cloud Run API**
   - **Cloud Build API**
   - **Container Registry API**

**Or use command line:**
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

---

## STEP 8: Login to Google Cloud

```bash
gcloud auth login
```

A browser window will open - click **"Allow"** to authorize.

Then set your project:
```bash
gcloud config set project YOUR_PROJECT_ID
```
(Replace `YOUR_PROJECT_ID` with your actual project ID)

---

## STEP 9: Deploy Backend to Cloud Run

Run this command (it will take 5-10 minutes):

```bash
gcloud run deploy stock-analyzer --source . --region us-central1 --platform managed --allow-unauthenticated --memory 512Mi --cpu 1 --timeout 300 --max-instances 10 --set-env-vars FINNHUB_API_KEY=d5l1bthr01qt47mg4io0d5l1bthr01qt47mg4iog,LOW_MEMORY_MODE=1
```

**What this does:**
- Builds your Flask app into a Docker container
- Deploys it to Cloud Run
- Makes it accessible via HTTPS
- Sets environment variables

**Wait for:** "Service [stock-analyzer] revision [stock-analyzer-xxxxx] has been deployed"

**Note the URL** shown (e.g., `https://stock-analyzer-xxxxx-uc.a.run.app`)

---

## STEP 10: Verify Cloud Run Service Name

After deployment, verify your service name matches what's in `firebase.json`:

1. Check `firebase.json` - it should have:
   ```json
   "serviceId": "stock-analyzer"
   ```

2. If your service name is different, update `firebase.json` to match

---

## STEP 11: Deploy Frontend to Firebase Hosting

```bash
firebase deploy --only hosting
```

**Wait for:** "Hosting URL: https://YOUR-PROJECT-ID.web.app"

---

## STEP 12: Test Your Website

1. Visit the URL shown after deployment (e.g., `https://stock-analyzer-12345.web.app`)
2. Test the application:
   - Enter a stock ticker (e.g., "AAPL")
   - Click submit
   - Verify charts and data load correctly

---

## Troubleshooting

### Problem: "Firebase CLI not found"
**Solution:** Make sure Node.js is installed and npm is in your PATH

### Problem: "gcloud: command not found"
**Solution:** Install Google Cloud SDK (Step 2) and restart your terminal

### Problem: "Permission denied" errors
**Solution:** Make sure you're logged in:
```bash
firebase login
gcloud auth login
```

### Problem: "API not enabled"
**Solution:** Enable the required APIs (Step 7)

### Problem: "Service not found" in Firebase Hosting
**Solution:** Make sure Cloud Run service name in `firebase.json` matches your deployed service

### Problem: Build fails
**Solution:** Check that all files are present:
- `Dockerfile` exists
- `requirements.txt` exists
- `wsgi.py` exists

---

## Quick Deploy Script (After Initial Setup)

Once everything is set up, you can use the PowerShell script:

```powershell
.\deploy-firebase.ps1
```

This will deploy both backend and frontend automatically.

---

## Updating Your Website

To update your website after making changes:

1. **Update backend:**
   ```bash
   gcloud run deploy stock-analyzer --source . --region us-central1
   ```

2. **Update frontend:**
   ```bash
   firebase deploy --only hosting
   ```

---

## Need Help?

- Firebase Docs: https://firebase.google.com/docs/hosting
- Cloud Run Docs: https://cloud.google.com/run/docs
- Check logs: `gcloud run services logs read stock-analyzer --region us-central1`
