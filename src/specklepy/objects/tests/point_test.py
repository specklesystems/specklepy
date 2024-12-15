from devtools import debug

from specklepy.api.operations import deserialize, serialize
from specklepy.objects.geometry import Point
from specklepy.objects.models.units import Units

# test points
p1 = Point(x=1.0, y=2.0, z=3.0, units=Units.m)
p2 = Point(x=4.0, y=6.0, z=8.0, units=Units.m, applicationId="asdf")

print("Distance between points:", p1.distance_to(p2))

ser_p1 = serialize(p1)
p1_again = deserialize(ser_p1)

print("\nOriginal point:")
debug(p1)
print("\nSerialized point:")
debug(ser_p1)
print("\nDeserialized point:")
debug(p1_again)
