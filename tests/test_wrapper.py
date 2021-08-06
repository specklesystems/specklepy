import pytest
from specklepy.api.credentials import StreamWrapper


class TestWrapper:
    def test_parse_stream(self):
        wrap = StreamWrapper("https://testing.speckle.dev/streams/a75ab4f10f")
        assert wrap.type == "stream"

    def test_parse_branch(self):
        wacky_wrap = StreamWrapper(
            "https://testing.speckle.dev/streams/4c3ce1459c/branches/%F0%9F%8D%95%E2%AC%85%F0%9F%8C%9F%20you%20wat%3F"
        )
        wrap = StreamWrapper(
            "https://testing.speckle.dev/streams/4c3ce1459c/branches/next%20level"
        )
        assert wacky_wrap.type == "branch"
        assert wacky_wrap.branch_name == "🍕⬅🌟 you wat?"
        assert wrap.type == "branch"

    def test_parse_commit(self):
        wrap = StreamWrapper(
            "https://testing.speckle.dev/streams/4c3ce1459c/commits/8b9b831792"
        )
        assert wrap.type == "commit"

    def test_parse_object(self):
        wrap = StreamWrapper(
            "https://testing.speckle.dev/streams/a75ab4f10f/objects/5530363e6d51c904903dafc3ea1d2ec6"
        )
        assert wrap.type == "object"

    def test_parse_globals_as_branch(self):
        wrap = StreamWrapper("https://testing.speckle.dev/streams/0c6ad366c4/globals/")
        assert wrap.type == "branch"

    def test_parse_globals_as_commit(self):
        wrap = StreamWrapper(
            "https://testing.speckle.dev/streams/0c6ad366c4/globals/abd3787893"
        )
        assert wrap.type == "commit"
