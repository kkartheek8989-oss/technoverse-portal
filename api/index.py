import os
import sys
from pathlib import Path

# Add project root to sys.path for Vercel Serverless environment
ROOT_DIR = str(Path(__file__).resolve().parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app
