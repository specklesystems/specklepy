"""
Provides uniform and consistent path helpers for `specklepy`
"""
import os
import sys
from pathlib import Path
from typing import Optional

from specklepy.logging.exceptions import SpeckleException

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


_blob_folder_name = "Blobs"


def override_blob_storage_folder(blob_folder_name: str) -> None:
    """Override the global Blob storage folder name."""
    global _blob_folder_name
    _blob_folder_name = blob_folder_name


_accounts_folder_name = "Accounts"


def override_accounts_folder_name(accounts_folder_name: str) -> None:
    """Override the global Accounts folder name."""
    global _accounts_folder_name
    _accounts_folder_name = accounts_folder_name


_objects_folder_name = "Objects"


def override_objects_folder_name(objects_folder_name: str) -> None:
    """Override global Objects folder name."""
    global _objects_folder_name
    _objects_folder_name = objects_folder_name


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
                raise SpeckleException(
                    message="Cannot get appdata path from environment."
                )
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
        raise SpeckleException(
            message="Failed to initialize user application data path.", exception=ex
        )


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


def accounts_folder_path() -> Path:
    """Get the folder where the Speckle accounts data should be stored."""
    return _ensure_folder_exists(user_speckle_folder_path(), _accounts_folder_name)


def blob_storage_path(path: Optional[Path] = None) -> Path:
    return _ensure_folder_exists(path or user_speckle_folder_path(), _blob_folder_name)
