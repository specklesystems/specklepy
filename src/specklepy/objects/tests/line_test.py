from devtools import debug
from specklepy.api.operations import deserialize, serialize
from specklepy.objects.geometry import Line, Point
from specklepy.objects.models.units import Units
from specklepy.objects.primitive import Interval


# points
p1 = Point(x=1.0, y=2.0, z=3.0, units=Units.m)
p2 = Point(x=4.0, y=6.0, z=8.0, units=Units.m, applicationId="asdf")


# test Line
line = Line(start=p1, end=p2, units=Units.m,
            domain=Interval(start=0.0, end=1.0))

print(f"\nLine length: {line.length}")

ser_line = serialize(line)
line_again = deserialize(ser_line)

print("\nOriginal line:")
debug(line)
print("\nSerialized line:")
debug(ser_line)
print("\nDeserialized line:")
debug(line_again)
