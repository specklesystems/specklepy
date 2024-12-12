from devtools import debug

from specklepy.api.operations import deserialize, serialize
from specklepy.objects_v3.geometry import Line, Point
from specklepy.objects_v3.models.units import Units
from specklepy.objects_v3.primitive import Interval

# test points
p1 = Point(x=1.0, y=2.0, z=3.0, units=Units.m)
p2 = Point(x=4.0, y=6.0, z=8.0, units=Units.m, applicationId="asdf")

p3 = Point(units="m", x=0, y=0, z=0)

print("Distance between points:", p1.distance_to(p2))

ser_p1 = serialize(p1)
p1_again = deserialize(ser_p1)

print("\nOriginal point:")
debug(p1)
print("\nSerialized point:")
debug(ser_p1)
print("\nDeserialized point:")
debug(p1_again)

# # test Line
line = Line(start=p1, end=p2, units=Units.m, domain=Interval(start=0.0, end=1.0))

# print(f"\nLine length: {line.length}")

ser_line = serialize(line)
line_again = deserialize(ser_line)

print("\nOriginal line:")
debug(line)
print("\nSerialized line:")
debug(ser_line)
print("\nDeserialized line:")
debug(line_again)
