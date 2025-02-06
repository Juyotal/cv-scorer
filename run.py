# This is my Root Module.
import os

from app.app import create_run
from config import CONFIG

if __name__ == '__main__':
    os.makedirs(CONFIG.DIRECTORIES.OUTPUT, exist_ok=True)
    create_run()
