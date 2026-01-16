# Quick Fix for Internal Server Error

## Step 1: Update Code
Run in PythonAnywhere **Bash Console**:
```bash
cd ~/stock-analyzer
git pull origin main
```

## Step 2: Create Data Directory
```bash
mkdir -p ~/stock-analyzer/data/cache
chmod 755 ~/stock-analyzer/data
chmod 755 ~/stock-analyzer/data/cache
```

## Step 3: Install Dependencies
```bash
cd ~/stock-analyzer
pip3 install --user --upgrade flask yfinance pandas plotly requests finnhub-python
```

## Step 4: Verify WSGI Configuration
1. Go to **Web** tab on PythonAnywhere
2. Click **WSGI configuration file** link
3. Make sure it contains:
```python
import sys
import os

project_home = '/home/danielzlatinski/stock-analyzer'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

cache_dir = os.path.join(project_home, "data", "cache")
os.makedirs(cache_dir, exist_ok=True)

os.environ['FLASK_DEBUG'] = '0'

from app import create_app
application = create_app()
```

## Step 5: Check Error Logs
1. Go to **Web** tab
2. Scroll to **Error log**
3. Click the link to view errors
4. Copy the error message

## Step 6: Test Endpoint
Visit: `https://danielzlatinski.pythonanywhere.com/test`

This will show what's working and what's broken.

## Step 7: Reload Web App
Click the big green **"Reload"** button on the Web tab.

## Common Issues:

### Issue: ModuleNotFoundError
**Fix:** Install missing package:
```bash
pip3 install --user <package-name>
```

### Issue: Permission denied
**Fix:** Check file permissions:
```bash
chmod 755 ~/stock-analyzer
chmod 755 ~/stock-analyzer/data/cache
```

### Issue: Import errors
**Fix:** Check Python version (should be 3.10):
```bash
python3 --version
```

### Issue: Cache directory errors
**Fix:** Create directory manually:
```bash
mkdir -p ~/stock-analyzer/data/cache
```
