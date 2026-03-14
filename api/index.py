import sys
import os

# Make the project root importable from this api/ subdirectory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: F401  — Vercel looks for a module-level `app` WSGI object
