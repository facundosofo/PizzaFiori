"""
Entry point for PyInstaller compilation.

Usage (development):
    python run.py

Build (from backend/ with venv active):
    pyinstaller pizzafiori.spec

The compiled exe reads all configuration (port, SSL certs) from the .env
file located next to the executable, so no command-line arguments are needed.
"""
import sys
import os
from pathlib import Path

# When running as a compiled PyInstaller bundle, change the working directory
# to the backend/ folder (parent of dist/) so that relative paths (./certs,
# ./logs, ./uploads, ./.env) resolve correctly regardless of how the service
# was launched.
if getattr(sys, 'frozen', False):
    os.chdir(Path(sys.executable).parent.parent)

import uvicorn
from app.infrastructure.config.settings import settings

if __name__ == '__main__':
    uvicorn.run(
        'app.main:app',
        host='0.0.0.0',
        port=settings.api_port,
        ssl_keyfile=settings.ssl_key_file,
        ssl_certfile=settings.ssl_cert_file,
        log_level='info',
    )
