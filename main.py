# This is my Root Module.
import atexit
import os
from app.app import create_run, cleanup_files
from config import CONFIG


if __name__ == '__main__':
    os.makedirs(CONFIG.DIRECTORIES.OUTPUT, exist_ok=True)
    create_run()
    atexit.register(cleanup_files)
