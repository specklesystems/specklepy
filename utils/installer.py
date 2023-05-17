"""
Provides uniform and consistent path helpers for `specklepy`
"""
import os
import sys
from importlib import import_module, invalidate_caches
from pathlib import Path
from typing import Optional

import pkg_resources

_user_data_env_var = "SPECKLE_USERDATA_PATH"


def _path() -> Optional[Path]:
    """Read the user data path override setting."""
    path_override = os.environ.get(_user_data_env_var)
    if path_override:
        return Path(path_override)
    return None


_application_name = "Speckle"


def override_application_name(application_name: str) -> None:
    """Override the global Speckle application name."""
    global _application_name
    _application_name = application_name


def override_application_data_path(path: Optional[str]) -> None:
    """
    Override the global Speckle application data path.

    If the value of path is `None` the environment variable gets deleted.
    """
    if path:
        os.environ[_user_data_env_var] = path
    else:
        os.environ.pop(_user_data_env_var, None)


def _ensure_folder_exists(base_path: Path, folder_name: str) -> Path:
    path = base_path.joinpath(folder_name)
    path.mkdir(exist_ok=True, parents=True)
    return path


def user_application_data_path() -> Path:
    """Get the platform specific user configuration folder path"""
    path_override = _path()
    if path_override:
        return path_override

    try:
        if sys.platform.startswith("win"):
            app_data_path = os.getenv("APPDATA")
            if not app_data_path:
                raise Exception("Cannot get appdata path from environment.")
            return Path(app_data_path)
        else:
            # try getting the standard XDG_DATA_HOME value
            # as that is used as an override
            app_data_path = os.getenv("XDG_DATA_HOME")
            if app_data_path:
                return Path(app_data_path)
            else:
                return _ensure_folder_exists(Path.home(), ".config")
    except Exception as ex:
        raise Exception("Failed to initialize user application data path.", ex)


def user_speckle_folder_path() -> Path:
    """Get the folder where the user's Speckle data should be stored."""
    return _ensure_folder_exists(user_application_data_path(), _application_name)


def user_speckle_connector_installation_path(host_application: str) -> Path:
    """
    Gets a connector specific installation folder.

    In this folder we can put our connector installation and all python packages.
    """
    return _ensure_folder_exists(
        _ensure_folder_exists(user_speckle_folder_path(), "connector_installations"),
        host_application,
    )


print("Starting module dependency installation")
print(sys.executable)

PYTHON_PATH = sys.executable


def connector_installation_path(host_application: str) -> Path:
    connector_installation_path = user_speckle_connector_installation_path(
        host_application
    )
    connector_installation_path.mkdir(exist_ok=True, parents=True)

    # set user modules path at beginning of paths for earlier hit
    if sys.path[0] != connector_installation_path:
        sys.path.insert(0, str(connector_installation_path))

    print(f"Using connector installation path {connector_installation_path}")
    return connector_installation_path


def is_pip_available() -> bool:
    try:
        import_module("pip")  # noqa F401
        return True
    except ImportError:
        return False


def ensure_pip() -> None:
    print("Installing pip... ")

    from subprocess import run

    completed_process = run([PYTHON_PATH, "-m", "ensurepip"])

    if completed_process.returncode == 0:
        print("Successfully installed pip")
    else:
        raise Exception(
            f"Failed to install pip, got {completed_process.returncode} return code"
        )


def get_requirements_path() -> Path:
    # we assume that a requirements.txt exists next to the __init__.py file
    path = Path(__file__).parent.with_name("requirements.txt")
    assert path.exists(), f"Can't find requirements file at {path}"
    return path


def install_requirements(host_application: str) -> None:
    # set up addons/modules under the user
    # script path. Here we'll install the
    # dependencies
    path = connector_installation_path(host_application)
    print(f"Installing Speckle dependencies to {path}")

    from subprocess import run

    completed_process = run(
        [
            PYTHON_PATH,
            "-m",
            "pip",
            "install",
            "-t",
            str(path),
            "-r",
            str(get_requirements_path()),
        ],
        capture_output=True,
        text=True,
    )

    if completed_process.returncode != 0:
        m = (
            "Failed to install dependenices through pip, ",
            f"got {completed_process.returncode} return code",
        )
        print(m)
        raise Exception(m)


def install_dependencies(host_application: str) -> None:
    if not is_pip_available():
        ensure_pip()

    install_requirements(host_application)


def _dependencies_installed() -> bool:
    try:
        pkg_resources.require(get_requirements_path().read_text())
        return True
    except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
        return False


def ensure_dependencies(host_application: str) -> None:
    if _dependencies_installed():
        return

    install_dependencies(host_application)
    invalidate_caches()
    if _dependencies_installed():
        print("Successfully found dependencies")
        return

    raise Exception(
        "Cannot automatically ensure Speckle dependencies. ",
        f"Please try restarting the host application {host_application}!",
    )
