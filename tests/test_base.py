import pytest
from speckle.objects.base import Base


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

