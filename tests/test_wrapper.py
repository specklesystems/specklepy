import pytest
from specklepy.api.wrapper import StreamWrapper


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


#! NOTE: the following three tests may not pass locally if you have a `speckle.xyz` account in manager
def test_get_client_without_auth():
    wrap = StreamWrapper("https://speckle.xyz/streams/4c3ce1459c/commits/8b9b831792")
    client = wrap.get_client()

    assert client is not None


def test_get_new_client_with_token():
    wrap = StreamWrapper("https://speckle.xyz/streams/4c3ce1459c/commits/8b9b831792")
    client = wrap.get_client()
    client = wrap.get_client(token="super-secret-token")

    assert client.account.token == "super-secret-token"


def test_get_transport_with_token():
    wrap = StreamWrapper("https://speckle.xyz/streams/4c3ce1459c/commits/8b9b831792")
    client = wrap.get_client()
    assert not client.me  # unauthenticated bc no local accounts

    transport = wrap.get_transport(token="super-secret-token")

    assert transport is not None
    assert client.account.token == "super-secret-token"
