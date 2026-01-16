# Deployment Guide - PythonAnywhere

## Step 1: Create PythonAnywhere Account
1. Go to **https://www.pythonanywhere.com**
2. Click **"Start running Python online"** → **"Create a Beginner account"** (FREE)
3. Sign up with your email

## Step 2: Upload Your Code

### Option A: Using Git (Recommended)
1. In PythonAnywhere, go to **Consoles** tab → Click **"Bash"**
2. Run:
```bash
cd ~
git clone https://github.com/DanielZlatinski/stock-analyzer.git
cd stock-analyzer
```

### Option B: Manual Upload
1. Go to **Files** tab
2. Navigate to `/home/yourusername/`
3. Create folder `stock-analyzer`
4. Upload all files from your local project

## Step 3: Install Dependencies
1. Go to **Consoles** → **Bash**
2. Run:
```bash
cd ~/stock-analyzer
pip3 install --user -r requirements.txt
```

## Step 4: Create Web App
1. Go to **Web** tab
2. Click **"Add a new web app"**
3. Click **Next** (accept free subdomain)
4. Select **"Flask"**
5. Select **Python 3.10** (or latest available)
6. Set path to: `/home/yourusername/stock-analyzer/wsgi.py`

## Step 5: Configure WSGI File
1. On **Web** tab, click the **WSGI configuration file** link
2. **Delete everything** and paste:
```python
import sys
import os

project_home = '/home/yourusername/stock-analyzer'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['FLASK_DEBUG'] = '0'

from app import create_app
application = create_app()
```
3. **Replace `yourusername`** with your actual PythonAnywhere username
4. **Save** (Ctrl+S)

## Step 6: Configure Static Files
1. On **Web** tab, scroll to **Static files**
2. Click **"Add a new static files mapping"**
3. Set:
   - **URL:** `/static/`
   - **Directory:** `/home/yourusername/stock-analyzer/static`

## Step 7: Set Environment Variables (Optional)
1. On **Web** tab, scroll to **Environment variables**
2. Add:
   - **Name:** `FINNHUB_API_KEY`
   - **Value:** `d5l1bthr01qt47mg4io0d5l1bthr01qt47mg4iog`

## Step 8: Create Cache Directory
1. Go to **Consoles** → **Bash**
2. Run:
```bash
cd ~/stock-analyzer
mkdir -p data/cache
```

## Step 9: Launch! 🚀
1. Click the big green **"Reload"** button on the Web tab
2. Visit: **`https://yourusername.pythonanywhere.com`**

## Troubleshooting
- **500 Error:** Check the **Error log** on Web tab
- **Charts not showing:** Make sure Plotly is installed (`pip3 install --user plotly`)
- **Import errors:** Check that all dependencies are installed
- **Static files not loading:** Verify static files mapping is correct

## Your Live URL
After deployment, your app will be live at:
**https://yourusername.pythonanywhere.com**
