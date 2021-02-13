import pytest
from speckle.objects.base import Base
from speckle.api import operations


@pytest.mark.parametrize(
    "invalid_prop_name",
    [
        (""),
        ("@"),
        ("@@wow"),
        ("this.is.bad"),
        ("super/bad"),
    ],
)
def test_empty_prop_names(invalid_prop_name: str) -> None:
    base = Base()
    with pytest.raises(ValueError):
        base[invalid_prop_name] = "🐛️"



class FakeBase(Base):
    """Just a test class type."""
    foo: str = ""

def test_new_type_registration() -> None:
    """Test if a new subclass is registered into the type register."""
    assert Base.get_registered_type("FakeBase") == FakeBase
    assert Base.get_registered_type("🐺️") is None

def test_fake_base_serialization() -> None:
    fake_model = FakeBase(foo="bar")


    serialized = operations.serialize(fake_model)
    deserialized = operations.deserialize(serialized)

    assert fake_model.get_id() == deserialized.get_id()


def test_duplicate_speckle_type_raises_error():
    with pytest.raises(ValueError):
        class NaughtyClass(Base, speckle_type="Base"):
            """This class has a speckle_type that is already taken."""