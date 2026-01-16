#!/bin/bash
# Quick fix script for PythonAnywhere deployment

echo "Setting up deployment..."

# Navigate to project directory
cd ~/stock-analyzer

# Create data directory if it doesn't exist
mkdir -p data/cache
chmod 755 data
chmod 755 data/cache

# Install/upgrade dependencies
pip3 install --user --upgrade -r requirements.txt

# Verify critical packages
echo "Checking packages..."
python3 -c "import flask; print('Flask:', flask.__version__)"
python3 -c "import yfinance; print('yfinance: OK')"
python3 -c "import plotly; print('Plotly:', plotly.__version__)"
python3 -c "import pandas; print('Pandas:', pandas.__version__)"

echo ""
echo "Setup complete! Now reload your web app on PythonAnywhere."
