import sys
import os

# Add chatbot folder to path
path = '/home/Mohamedfaas/mysite/chatbot'
if path not in sys.path:
    sys.path.insert(0, path)

os.chdir(path)

from app import app as application
