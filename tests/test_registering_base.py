from typing import Type

import pytest

from specklepy.objects.base import Base
from specklepy.objects.structural import Concrete


class Foo(Base):
    """This is a Foo inheriting from Base."""


class Bar(Foo, speckle_type="Custom.Bar"):
    """This is a Bar inheriting from Foo."""


class Baz(Bar):
    """This is a Bar inheriting from Foo."""


@pytest.mark.parametrize(
    "klass, speckle_type",
    [
        (Base, "Base"),
        (Foo, "Foo"),
        (Bar, "Foo:Custom.Bar"),
        (Baz, "Foo:Custom.Bar:Baz"),
        (
            Concrete,
            "Objects.Structural.Materials.StructuralMaterial:Objects.Structural.Materials.Concrete",
        ),
    ],
)
def test_determine_speckle_type(klass: Type[Base], speckle_type: str):
    assert klass._determine_speckle_type() == speckle_type
