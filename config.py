import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class CONFIG:
    """This class is responsible for holding all the configuration variables for the Project."""
    ENV_CREDENTIALS = os.environ.copy()

    class DIRECTORIES:
        """This class serves as a container for any directories you require for your Project.

        These will be created automatically
        """
        OUTPUT = Path().cwd() / 'output'
