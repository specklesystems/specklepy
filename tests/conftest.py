import random

import pytest

from specklepy.objects.base import Base


@pytest.fixture(scope="session")
def base() -> Base:
    base = Base()
    base.name = "my_base"
    base.units = "millimetres"
    base.null_val = None
    base.null_dict = {"a null val": None}
    base.tuple = (1, 2, "3")
    base.set = {1, 2, "3"}
    base.vertices = [random.uniform(0, 10) for _ in range(1, 120)]
    base.test_bases = [Base(applicationId=str(i)) for i in range(1, 22)]
    base["@detach"] = Base(applicationId="detached base")
    base["@revit_thing"] = Base.of_type(
        "SpecialRevitFamily", applicationId="secret tho"
    )
    return base
