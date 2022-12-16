from enum import Enum, IntEnum
import pytest
from typing import Any, Dict, List, Optional, Tuple
from specklepy.objects.base import Base, _validate_type

test_base = Base()


class FakeEnum(Enum):
    foo = "foo"
    bar = "bar"


class FakeIntEnum(IntEnum):
    one = 1


@pytest.mark.parametrize(
    "input_type, value, is_valid, return_value",
    [
        (str, 10, True, "10"),
        (str, "foo_bar", True, "foo_bar"),
        (
            str,
            {"foo": "bar"},
            True,
            "{'foo': 'bar'}",
        ),
        # why are we allowing this??? We're lying to our users and ourselves too.
        (str, None, True, None),
        (bool, None, True, None),
        # any value is allowed for Any
        (Any, "foo", True, "foo"),
        (Any, test_base, True, test_base),
        # any value is allowed for None as a type. Why is none as a type allowed?
        (None, True, True, True),
        (None, "True", True, "True"),
        (None, {"foo": 1}, True, {"foo": 1}),
        (FakeEnum, FakeEnum.bar, True, FakeEnum.bar),
        (FakeEnum, FakeEnum.bar.value, True, FakeEnum.bar),
        (FakeEnum, "baz", False, "baz"),
        (FakeIntEnum, FakeIntEnum.one.value, True, FakeIntEnum.one),
        (FakeIntEnum, FakeIntEnum.one, True, FakeIntEnum.one),
        (FakeIntEnum, 2, False, 2),
        (FakeIntEnum, 123., False, 123.),
        (Base, test_base, True, test_base),
        (Base, 123, False, 123),
        (Optional[int], 1, True, 1),
        (Optional[int], None, True, None),
        (Optional[FakeEnum], None, True, None),
        (Optional[FakeEnum], FakeEnum.bar, True, FakeEnum.bar),
        (Optional[FakeEnum], FakeEnum.bar.value, True, FakeEnum.bar),
        (Optional[FakeEnum], "baz", False, "baz"),
        (Optional[Base], test_base, True, test_base),
        (Optional[Base], None, True, None),
        (List[int], [1, 2], True, [1, 2]),
        (List[int], ["1", 2], False, ["1", 2]),
        # same as the dict typing below...
        (List[int], [None, 2], True, [None, 2]),
        (List[Optional[int]], [None, 2], True, [None, 2]),
        (Dict[str, int], {"foo": 1}, True, {"foo": 1}),
        (Dict[str, Optional[int]], {"foo": None}, True, {"foo": None}),
        # this case should be
        # (Dict[int, Base], {1: None}, False, {1: None}),
        # but type checking currently allows everything to be None
        (Dict[int, Base], {1: None}, True, {1: None}),
        (Dict[int, Base], {1: test_base}, True, {1: test_base}),
        (Tuple[int, str, str], (1, "foo", "bar"), True, (1, "foo", "bar")),
        # given our current rules, this is the reality. Its just sad...
        (Tuple[str, str, str], (1, "foo", "bar"), True, ("1", "foo", "bar")),
        (Tuple[str, Optional[str], str], (1, None, "bar"), True, ("1", None, "bar")),
    ],
)
def test_validate_type(
    input_type: type, value: Any, is_valid: bool, return_value: Any
) -> None:
    assert (is_valid, return_value) == _validate_type(input_type, value)
