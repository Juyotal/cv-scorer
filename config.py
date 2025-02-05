from pathlib import Path
from tempfile import TemporaryDirectory


class Config:
    """This class is responsible for holding all the configuration variables for the Project."""

    class DIRECTORIES:
        """This class serves as a container for any directories you require for your Project.

        These will be created automatically
        """
        TEMP = Path(TemporaryDirectory().name)
        OUTPUT = Path().cwd() / "output"
