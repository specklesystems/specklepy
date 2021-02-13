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
    # assert isinstance(base.test_bases[0], Base)
    # assert base["@detach"].name == deserialized["@detach"].name