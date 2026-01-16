# WSGI entry point for PythonAnywhere deployment
import sys
import os

# Add your project directory to the sys.path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Ensure data/cache directory exists
cache_dir = os.path.join(project_home, "data", "cache")
os.makedirs(cache_dir, exist_ok=True)

# Set environment variables for production
os.environ['FLASK_DEBUG'] = '0'

# Import Flask application
try:
    from app import create_app
    application = create_app()
except Exception as e:
    # If there's an import error, create a simple error app
    from flask import Flask
    error_app = Flask(__name__)
    
    @error_app.route('/')
    def error():
        import traceback
        return f"""
        <h1>Application Error</h1>
        <p>Failed to import application:</p>
        <pre>{str(e)}</pre>
        <pre>{traceback.format_exc()}</pre>
        """
    
    application = error_app
