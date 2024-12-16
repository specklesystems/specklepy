from devtools import debug
from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry import Polyline
from specklepy.objects.models.units import Units
from specklepy.objects.primitive import Interval


# create points for first polyline - not closed, in meters
points1_coords = [
    1.0, 1.0, 0.0,
    2.0, 1.0, 0.0,
    2.0, 2.0, 0.0,
    1.0, 2.0, 0.0
]

# Create points for second polyline - closed, in ft
points2_coords = [
    0.0, 0.0, 0.0,
    3.0, 0.0, 0.0,
    3.0, 3.0, 0.0,
    0.0, 3.0, 0.0
]

# create polylines
polyline1 = Polyline(
    value=points1_coords,
    closed=False,
    units=Units.m,
    domain=Interval(start=0.0, end=1.0)
)

polyline2 = Polyline(
    value=points2_coords,
    closed=True,
    units=Units.feet,
    domain=Interval(start=0.0, end=1.0),
    applicationId="polyllllineeee"
)

print("Polyline 1 length (meters):", polyline1.length)
print("Polyline 2 length (feet):", polyline2.length)

ser_poly1 = serialize(polyline1)
poly1_again = deserialize(ser_poly1)

print("\nOriginal polyline 1:")
debug(polyline1)
print("\nSerialized polyline 1:")
debug(ser_poly1)
print("\nDeserialized polyline 1:")
debug(poly1_again)

ser_poly2 = serialize(polyline2)
poly2_again = deserialize(ser_poly2)

print("\nOriginal polyline 2:")
debug(polyline2)
print("\nSerialized polyline 2:")
debug(ser_poly2)
print("\nDeserialized polyline 2:")
debug(poly2_again)
