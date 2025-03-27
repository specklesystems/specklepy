from devtools import debug

from specklepy.api import operations
from specklepy.objects_v2.geometry import Base
from specklepy.objects_v2.units import Units

dct = {
    "id": "1234abcd",
    "units": None,
    "speckle_type": "Base",
    "applicationId": None,
    "totalChildrenCount": 0,
}
base = Base()
for prop, value in dct.items():
    base.__setattr__(prop, value)


debug(base)
debug(base.units)

base.units = "m"
debug(base.units)
base.units = None

debug(base.units)

foo = operations.serialize(base)

base.units = 10

debug(base.units)
debug(foo)

base.units = Units.mm
debug(base.units)
