import sys
from pathlib import Path
from appdirs import user_data_dir


def base_path(app_name) -> Path:
    # from appdirs https://github.com/ActiveState/appdirs/blob/master/appdirs.py
    # default mac path is not the one we use (we use unix path), so using special case for this
    system = sys.platform
    if system.startswith("java"):
        import platform

        os_name = platform.java_ver()[3][0]
        if os_name.startswith("Mac"):
            system = "darwin"

    if system == "darwin":
        return Path(Path.home(), ".config", app_name)

    return Path(user_data_dir(appname=app_name, appauthor=False, roaming=True))


def accounts_path(app_name: str = "Speckle") -> Path:
    """
    Gets the path where the Speckle applications are looking for accounts.
    """
    return base_path(app_name).joinpath("Accounts")
