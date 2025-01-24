from typing import Type

import pytest

from specklepy.objects.base import Base


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
        (Foo, "Tests.Unit.TestRegisteringBase.Foo"),
        (Bar, "Tests.Unit.TestRegisteringBase.Foo:Custom.Bar"),
        (
            Baz,
            "Tests.Unit.TestRegisteringBase.Foo:Custom.Bar:Tests.Unit.TestRegisteringBase.Baz",
        ),
    ],
)
def test_determine_speckle_type(klass: Type[Base], speckle_type: str):
    assert klass._determine_speckle_type() == speckle_type


@pytest.mark.parametrize(
    "klass, fully_qualified_name",
    [
        (Base, "Base"),
        (Foo, "Tests.Unit.TestRegisteringBase.Foo"),
    ],
)
def test_full_name(klass: Type[Base], fully_qualified_name: str):
    assert klass._full_name() == fully_qualified_name
