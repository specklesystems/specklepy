from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pytest

from specklepy.objects.base import Base, _validate_type
from specklepy.objects.primitive import Interval

test_base = Base()


class FakeEnum(Enum):
    foo = "foo"
    bar = "bar"


class FakeIntEnum(IntEnum):
    one = 1


class FakeBase(Base):
    foo: Optional[str]

    def __init__(self, foo: str) -> None:
        self.foo = foo


fake_bases = [FakeBase("foo"), FakeBase("bar")]


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
        (float, 1, True, 1),
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
        (FakeIntEnum, 123.0, False, 123.0),
        (Base, test_base, True, test_base),
        (Base, 123, False, 123),
        (Optional[int], 1, True, 1),
        # this is just silly...
        (Optional[int], [1, 2, 3], False, [1, 2, 3]),
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
        (List, ["foo", 2, "bar"], True, ["foo", 2, "bar"]),
        (Dict[str, int], {"foo": 1}, True, {"foo": 1}),
        (Dict, {"foo": 1}, True, {"foo": 1}),
        (Dict[str, Optional[int]], {"foo": None}, True, {"foo": None}),
        # this case should be
        # (Dict[int, Base], {1: None}, False, {1: None}),
        # but type checking currently allows everything to be None
        (Dict[int, Base], {1: None}, True, {1: None}),
        (Dict[int, Base], {1: test_base}, True, {1: test_base}),
        (Tuple[int, str, str], (1, "foo", "bar"), True, (1, "foo", "bar")),
        (Tuple, (1, "foo", "bar"), True, (1, "foo", "bar")),
        # given our current rules, this is the reality. Its just sad...
        (Tuple[str, str, str], (1, "foo", "bar"), True, ("1", "foo", "bar")),
        (Tuple[str, Optional[str], str], (1, None, "bar"), True, ("1", None, "bar")),
        (Set[bool], set([1, 2]), False, set([1, 2])),
        (Set[int], set([1, 2]), True, set([1, 2])),
        (Set[int], set([None, 2]), True, set([None, 2])),
        # not testing this, since order of input iterables in sets are not preserved
        # easily produces false reports since we're only checking the type of the
        # first item
        # (Set[int], set(["None", 2]), False, set(["None", 2])),
        (Set[Optional[int]], set([None, 2]), True, set([None, 2])),
        (Optional[Union[List[int], List[FakeBase]]], None, True, None),
        (Optional[Union[List[int], List[FakeBase]]], "foo", False, "foo"),
        (Union[List[int], List[FakeBase], None], "foo", False, "foo"),
        (Optional[Union[List[int], List[FakeBase]]], [1, 2, 3], True, [1, 2, 3]),
        (
            Optional[Union[List[int], List[FakeBase]]],
            fake_bases,
            True,
            fake_bases,
        ),
        (List["int"], [2, 3, 4], True, [2, 3, 4]),
        (
            Union[float, Dict[str, float]],
            {"foo": 1, "bar": 2},
            True,
            {"foo": 1.0, "bar": 2.0},
        ),
        (Union[float, Dict[str, float]], {"foo": "bar"}, False, {"foo": "bar"}),
    ],
)
def test_validate_type(
    input_type: type, value: Any, is_valid: bool, return_value: Any
) -> None:
    assert (is_valid, return_value) == _validate_type(input_type, value)


def test_intervar_type():
    i = Interval(start=5, end=10)
    assert i
