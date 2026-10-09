import sys
import os

# Passenger WSGI entrypoint for Hostinger Python App
sys.path.insert(0, os.path.dirname(__file__))

from app import app as application
