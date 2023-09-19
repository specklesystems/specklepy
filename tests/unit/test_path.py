import re
import sys
from pathlib import Path

from specklepy.core.helpers import speckle_path_provider


def test_user_application_data_path():
    user_path = str(speckle_path_provider.user_application_data_path())

    if sys.platform.startswith("win"):
        pattern = r"C:\\Users\\.*\\AppData\\Roaming"
    elif sys.platform.startswith("darwin"):
        pattern = "/Users/.*/.config"
    elif sys.platform.startswith("linux"):
        if user_path.startswith("/root"):
            pattern = "/root/.config"
        else:
            pattern = "/home/.*/.config"
    else:
        raise NotImplementedError("Your OS platform is not supported")

    match = re.search(pattern, user_path)
    assert match


def test_user_application_data_path_override():
    path = "/jiberish"
    speckle_path_provider.override_application_data_path(path)

    user_path = speckle_path_provider.user_application_data_path()
    assert Path(path) == user_path

    speckle_path_provider.override_application_data_path(None)

    user_path = speckle_path_provider.user_application_data_path()
    assert Path(path) != user_path


def test_accounts_folder_name_override():
    old_folder_name = speckle_path_provider._accounts_folder_name
    assert old_folder_name == "Accounts"
    new_folder_name = "foobar"
    speckle_path_provider.override_accounts_folder_name(new_folder_name)
    assert speckle_path_provider._accounts_folder_name == new_folder_name
    speckle_path_provider.override_accounts_folder_name(old_folder_name)


def test_connector_installation_path():
    host_application = "test application"
    connector_path = speckle_path_provider.user_speckle_connector_installation_path(
        host_application
    )
    assert "connector_installations" in str(connector_path)
    assert str(connector_path).endswith(host_application)
