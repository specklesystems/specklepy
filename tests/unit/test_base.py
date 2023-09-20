from contextlib import ExitStack as does_not_raise
from enum import Enum
from typing import Dict, List, Optional, Union

import pytest

from specklepy.api import operations
from specklepy.logging.exceptions import SpeckleException, SpeckleInvalidUnitException
from specklepy.objects.base import Base
from specklepy.objects.units import Units


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
    fake_model = FakeModel(foo="bar")

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
    base.speckle_type = "unset"
    assert base.speckle_type == "Base"


def test_setting_units():
    b = Base(units="foot")
    assert b.units == "foot"

    # with pytest.raises(SpeckleInvalidUnitException):
    b.units = "big"
    assert b.units == "big"

    with pytest.raises(SpeckleInvalidUnitException):
        b.units = 7  # invalid args are skipped
    assert b.units == "big"

    b.units = None  # None should be a valid arg
    assert b.units is None

    b.units = Units.none
    assert b.units == "none"

    b.units = Units.cm
    assert b.units == Units.cm.value


def test_base_of_custom_speckle_type() -> None:
    b1 = Base.of_type("BirdHouse", name="Tweety's Crib")
    assert b1.speckle_type == "BirdHouse"
    assert b1.name == "Tweety's Crib"


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
    order.price = "7"  # will get converted
    order.customer = "izzy"
    order.dietary = DietaryRestrictions.VEGAN
    order.tag = "preorder"
    order.tag = 4411

    with pytest.raises(SpeckleException):
        order.flavours = "not a list"
    with pytest.raises(SpeckleException):
        order.servings = "five"
    with pytest.raises(SpeckleException):
        order.add_ons = ["sprinkles"]
    with pytest.raises(SpeckleException):
        order.dietary = "no nuts plz"
    with pytest.raises(SpeckleException):
        order.tag = ["tag01", "tag02"]

    order.add_ons = {"sprinkles": 0.2, "chocolate": 1.0}
    order.flavours = ["strawberry", "lychee", "peach", "pineapple"]

    assert order.price == 7.0
    assert order.dietary == DietaryRestrictions.VEGAN


def test_cached_deserialization() -> None:
    material = Base(color="blue", opacity=0.5)

    a = Base(name="a")
    a["@material"] = material
    b = Base(name="b")
    b["@material"] = material

    root = Base(a=a, b=b)

    serialized = operations.serialize(root)
    deserialized = operations.deserialize(serialized)

    assert deserialized["a"]["@material"] is deserialized["b"]["@material"]


def test_translations() -> None:
    speckle_type_override = "TrickyToTranslate"
    translated_speckle_type = "ItMeansThis🪂"

    maybe_type = Base.get_registered_type(speckle_type_override)

    assert maybe_type == None

    class TrickyToTranslate(
        Base,
        speckle_type=speckle_type_override,
        speckle_type_translations=[translated_speckle_type],
    ):
        """This is just a test class with no body."""

    maybe_type = Base.get_registered_type(speckle_type_override)
    assert maybe_type == TrickyToTranslate

    maybe_type = Base.get_registered_type(translated_speckle_type)
    assert maybe_type == TrickyToTranslate
