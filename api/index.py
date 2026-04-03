import os
import sys

# Add the 'backend' directory to the Python path so imports from 'app' work correctly.
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.main import app
