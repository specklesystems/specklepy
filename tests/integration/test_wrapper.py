import contextlib
import json
import tempfile
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote

import pytest

from specklepy.api.wrapper import StreamWrapper
from specklepy.core.helpers import speckle_path_provider
from specklepy.logging.exceptions import SpeckleException


@pytest.fixture(scope="module", autouse=True)
def user_path() -> Iterable[Path]:
    speckle_path_provider.override_application_data_path(tempfile.gettempdir())
    path = speckle_path_provider.accounts_folder_path().joinpath("test_acc.json")
    # hey, py37 doesn't support the missing_ok argument
    with contextlib.suppress(Exception):
        path.unlink()

    with contextlib.suppress(Exception):
        path.unlink(missing_ok=True)
    path.parent.absolute().mkdir(exist_ok=True)
    yield path
    if path.exists():
        path.unlink()
    speckle_path_provider.override_application_data_path(None)


def test_parse_empty():
    try:
        StreamWrapper("https://testing.speckle.dev/streams")
        raise AssertionError()
    except SpeckleException:
        assert True


def test_parse_empty_fe2():
    try:
        StreamWrapper("https://latest.speckle.systems/projects")
        raise AssertionError()
    except SpeckleException:
        assert True


def test_parse_stream():
    wrap = StreamWrapper("https://testing.speckle.dev/streams/a75ab4f10f")
    assert wrap.type == "stream"


def test_parse_branch():
    wacky_wrap = StreamWrapper(
        "https://testing.speckle.dev/streams/4c3ce1459c/branches/%F0%9F%8D%95%E2%AC%85%F0%9F%8C%9F%20you%20wat%3F"
    )
    wrap = StreamWrapper(
        "https://testing.speckle.dev/streams/4c3ce1459c/branches/next%20level"
    )
    assert wacky_wrap.type == "branch"
    assert wacky_wrap.branch_name == "🍕⬅🌟 you wat?"
    assert wrap.type == "branch"


def test_parse_nested_branch():
    wrap = StreamWrapper(
        "https://testing.speckle.dev/streams/4c3ce1459c/branches/izzy/dev"
    )

    assert wrap.branch_name == "izzy/dev"
    assert wrap.type == "branch"


def test_parse_commit():
    wrap = StreamWrapper(
        "https://testing.speckle.dev/streams/4c3ce1459c/commits/8b9b831792"
    )
    assert wrap.type == "commit"


def test_parse_object():
    wrap = StreamWrapper(
        "https://testing.speckle.dev/streams/a75ab4f10f/objects/5530363e6d51c904903dafc3ea1d2ec6"
    )
    assert wrap.type == "object"


def test_parse_globals_as_branch():
    wrap = StreamWrapper("https://testing.speckle.dev/streams/0c6ad366c4/globals/")
    assert wrap.type == "branch"


def test_parse_globals_as_commit():
    wrap = StreamWrapper(
        "https://testing.speckle.dev/streams/0c6ad366c4/globals/abd3787893"
    )
    assert wrap.type == "commit"


#! NOTE: the following three tests may not pass locally
# if you have a `app.speckle.systems` account in manager
def test_get_client_without_auth():
    wrap = StreamWrapper(
        "https://app.speckle.systems/streams/4c3ce1459c/commits/8b9b831792"
    )
    client = wrap.get_client()

    assert client is not None


def test_get_new_client_with_token(user_path):
    wrap = StreamWrapper(
        "https://app.speckle.systems/streams/4c3ce1459c/commits/8b9b831792"
    )
    client = wrap.get_client()
    client = wrap.get_client(token="super-secret-token")

    assert client.account.token == "super-secret-token"


def test_get_transport_with_token():
    wrap = StreamWrapper(
        "https://app.speckle.systems/streams/4c3ce1459c/commits/8b9b831792"
    )
    client = wrap.get_client()
    assert not client.account.token  # unauthenticated bc no local accounts

    transport = wrap.get_transport(token="super-secret-token")

    assert transport is not None
    assert client.account.token == "super-secret-token"


def test_wrapper_url_match(user_path) -> None:
    """
    The stream wrapper should only recognize exact url matches for the account
    definitions and not match for subdomains.
    """
    account = {
        "token": "foobar",
        "serverInfo": {"name": "foo", "url": "http://foo.bar.baz", "company": "Foo"},
        "userInfo": {"id": "bla", "name": "A rando tester", "email": "rando@tester.me"},
    }

    user_path.write_text(json.dumps(account))
    wrap = StreamWrapper("http://bar.baz/streams/bogus")

    account = wrap.get_account()

    assert account.userInfo.email is None


def test_parse_project():
    wrap = StreamWrapper("https://latest.speckle.systems/projects/843d07eb10")
    assert wrap.type == "stream"


def test_parse_model():
    wrap = StreamWrapper(
        "https://latest.speckle.systems/projects/843d07eb10/models/d9eb4918c8"
    )

    assert wrap.branch_name == "building wrapper"
    assert wrap.type == "branch"


def test_parse_federated_model():
    try:
        StreamWrapper("https://latest.speckle.systems/projects/843d07eb10/models/$main")
        raise AssertionError()
    except SpeckleException:
        assert True


def test_parse_multi_model():
    try:
        StreamWrapper(
            "https://latest.speckle.systems/projects/2099ac4b5f/models/1870f279e3,a9cfdddc79"
        )
        raise AssertionError()
    except SpeckleException:
        assert True


def test_parse_object_fe2():
    wrap = StreamWrapper(
        "https://latest.speckle.systems/projects/24c3741255/models/b48d1b10f5a732f4ca4144286391282c"
    )
    assert wrap.type == "object"


def test_parse_version():
    wrap = StreamWrapper(
        "https://latest.speckle.systems/projects/843d07eb10/models/4e7345c838@c42d5cbac1"
    )
    wrap_quoted = StreamWrapper(
        "https://latest.speckle.systems/projects/843d07eb10/models/4e7345c838%40c42d5cbac1"
    )
    assert wrap.type == "commit"
    assert wrap_quoted.type == "commit"


def test_to_string():
    urls = [
        "https://testing.speckle.dev/streams/a75ab4f10f",
        "https://testing.speckle.dev/streams/4c3ce1459c/branches/%F0%9F%8D%95%E2%AC%85%F0%9F%8C%9F%20you%20wat%3F",
        "https://testing.speckle.dev/streams/0c6ad366c4/globals",
        "https://testing.speckle.dev/streams/0c6ad366c4/globals/abd3787893",
        "https://testing.speckle.dev/streams/4c3ce1459c/commits/8b9b831792",
        "https://testing.speckle.dev/streams/a75ab4f10f/objects/5530363e6d51c904903dafc3ea1d2ec6",
        "https://latest.speckle.systems/projects/843d07eb10",
        "https://latest.speckle.systems/projects/843d07eb10/models/4e7345c838",
        "https://latest.speckle.systems/projects/843d07eb10/models/4e7345c838@c42d5cbac1",
        "https://latest.speckle.systems/projects/843d07eb10/models/4e7345c838%40c42d5cbac1",
        "https://latest.speckle.systems/projects/24c3741255/models/b48d1b10f5a732f4ca4144286391282c",
    ]
    for url in urls:
        wrap = StreamWrapper(url)
        assert unquote(wrap.to_string()) == unquote(url)
