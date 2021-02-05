import pytest
from speckle.objects.base import Base


class TestBase:
    def test_empty_prop_names(self):
        base = Base()
        with pytest.raises(ValueError):
            base[""] = "empty"
        with pytest.raises(ValueError):
            base["@"] = "empty"

    def test_invalid_prop_names(self):
        base = Base()

        with pytest.raises(ValueError):
            base["@@wow"] = "bad"

        with pytest.raises(ValueError):
            base["this.is.bad"] = "also bad"

        with pytest.raises(ValueError):
            base["super/bad"] = "no no no"
