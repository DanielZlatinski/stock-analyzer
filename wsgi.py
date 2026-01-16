# WSGI entry point for PythonAnywhere deployment
import sys
import os

# Add your project directory to the sys.path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables for production
os.environ['FLASK_DEBUG'] = '0'

# Import Flask application
from app import create_app

application = create_app()
