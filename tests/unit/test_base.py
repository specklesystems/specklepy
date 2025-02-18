from contextlib import ExitStack as does_not_raise
from enum import Enum
from typing import Dict, List, Optional, Union

import pytest

from specklepy.api import operations
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.base import Base
from specklepy.objects.interfaces import IHasUnits
from specklepy.objects.models.units import Units


@pytest.mark.parametrize(
    "invalid_prop_name",
    [
        "",
        "@",
        "@@wow",
        "this.is.bad",
        "super/bad",
    ],
)
def test_empty_prop_names(invalid_prop_name: str) -> None:
    base = Base()
    with pytest.raises(ValueError):
        base[invalid_prop_name] = "🐛️"


class FakeModel(Base):
    """Just a test class type."""


class FakeSub(FakeModel):
    """Just a test class type."""


def test_new_type_registration() -> None:
    """Test if a new subclass is registered into the type register."""
    assert Base.get_registered_type(FakeModel.speckle_type) == FakeModel
    assert Base.get_registered_type(FakeSub.speckle_type) == FakeSub
    assert Base.get_registered_type("🐺️") is None


def test_fake_base_serialization() -> None:
    fake_model = FakeModel()
    fake_model.foo = "bar"

    serialized = operations.serialize(fake_model)
    deserialized = operations.deserialize(serialized)

    assert fake_model.get_id() == deserialized.get_id()


def test_duplicate_speckle_type_raises_error():
    with pytest.raises(ValueError):

        class NaughtyClass(Base, speckle_type="Base"):
            """This class has a speckle_type that is already taken."""


@pytest.mark.parametrize(
    "forbidden_attribute_name, expectation",
    [
        ("", pytest.raises(ValueError)),
        ("@", pytest.raises(ValueError)),
        ("@@", pytest.raises(ValueError)),
        ("im.cheeky", pytest.raises(ValueError)),
        ("im.cheeky", pytest.raises(ValueError)),
        ("imgood", does_not_raise()),
    ],
)
def test_attribute_name_validation(
    forbidden_attribute_name: str,
    expectation,
    base: Base,
):
    with expectation:
        base[forbidden_attribute_name] = None


def test_speckle_type_cannot_be_set(base: Base) -> None:
    assert base.speckle_type == "Base"
    base.speckle_type = "unset"  # type: ignore
    assert base.speckle_type == "Base"


class FakeUnitBase(Base, IHasUnits, speckle_type="UnityBase"):
    pass


def test_setting_units():
    b = FakeUnitBase()
    b.units = "foot"
    assert b.units == "foot"

    # with pytest.raises(SpeckleInvalidUnitException):
    b.units = "big"
    assert b.units == "big"

    # invalid args are skipped
    with pytest.raises(SpeckleException):
        b.units = 7  # type: ignore
    assert b.units == "big"

    # None should be not be a valid arg
    with pytest.raises(SpeckleException):
        b.units = None  # type: ignore
    assert b.units == "big"

    b.units = Units.none
    assert b.units == "none"

    b.units = Units.cm
    assert b.units == Units.cm.value


def test_base_of_custom_speckle_type() -> None:
    b1 = Base.of_type("BirdHouse", applicationId="Tweety's Crib")
    assert b1.speckle_type == "BirdHouse"
    assert b1.applicationId == "Tweety's Crib"


class DietaryRestrictions(Enum):
    VEGAN = 1
    GLUTEN_FREE = 2
    NUT_FREE = 3


class FrozenYoghurt(Base):
    """Testing type checking"""

    servings: int
    flavours: List[str]  # list item types won't be checked
    customer: str
    add_ons: Optional[Dict[str, float]]  # dict item types won't be checked
    price: float = 0.0
    dietary: DietaryRestrictions
    tag: Union[int, str]


def test_type_checking() -> None:
    order = FrozenYoghurt()

    order.servings = 2
    order.price = "7"  # type: ignore - it will get converted
    order.customer = "izzy"
    order.dietary = DietaryRestrictions.VEGAN
    order.tag = "preorder"
    order.tag = 4411

    with pytest.raises(SpeckleException):
        order.flavours = "not a list"  # type: ignore
    with pytest.raises(SpeckleException):
        order.servings = "five"  # type: ignore
    with pytest.raises(SpeckleException):
        order.add_ons = ["sprinkles"]  # type: ignore
    with pytest.raises(SpeckleException):
        order.dietary = "no nuts plz"  # type: ignore
    with pytest.raises(SpeckleException):
        order.tag = ["tag01", "tag02"]  # type: ignore

    order.add_ons = {"sprinkles": 0.2, "chocolate": 1.0}
    order.flavours = ["strawberry", "lychee", "peach", "pineapple"]

    assert order.price == 7.0
    assert order.dietary == DietaryRestrictions.VEGAN


def test_cached_deserialization() -> None:
    material = Base()
    material.color = "blue"
    material.opacity = 0.5

    a = Base()
    a.name = "a"
    a["@material"] = material

    b = Base()
    b.name = "b"
    b["@material"] = material

    root = Base()
    root.a = a
    root.b = b

    serialized = operations.serialize(root)
    deserialized = operations.deserialize(serialized)

    assert deserialized["a"]["@material"] is deserialized["b"]["@material"]
