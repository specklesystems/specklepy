from devtools import debug

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry import Plane, Point, Vector
from specklepy.objects.other import Transform
from specklepy.objects.models.units import Units, get_encoding_from_units

# Create test points and vectors
origin = Point(x=0.0, y=0.0, z=0.0, units=Units.m)
normal = Vector(x=0.0, y=0.0, z=1.0, units=Units.m)
xdir = Vector(x=1.0, y=0.0, z=0.0, units=Units.m)
ydir = Vector(x=0.0, y=1.0, z=0.0, units=Units.m)

# Create test plane
plane = Plane(
    origin=origin,
    normal=normal,
    xdir=xdir,
    ydir=ydir,
    units=Units.m,
    applicationId="test_plane"
)

print("\nOriginal Plane:")
debug(plane)

# Test serialization
serialized_plane = serialize(plane)
deserialized_plane = deserialize(serialized_plane)

print("\nSerialized plane:")
debug(serialized_plane)
print("\nDeserialized plane:")
debug(deserialized_plane)

# Test transform
transform_matrix = [
    2.0, 0.0, 0.0, 1.0,  # Scale x by 2, translate x by 1
    0.0, 2.0, 0.0, 2.0,  # Scale y by 2, translate y by 2
    0.0, 0.0, 2.0, 3.0,  # Scale z by 2, translate z by 3
    0.0, 0.0, 0.0, 1.0
]

transform = Transform(matrix=transform_matrix, units="m")

print("\nTransform:")
debug(transform)

success, transformed_plane = plane.transform_to(transform)

print("\nTransformed plane:")
debug(transformed_plane)

# Test to_list and from_list
plane_list = plane.to_list()
reconstructed_plane = Plane.from_list(plane_list)

print("\nPlane as list:")
debug(plane_list)
print("\nReconstructed plane from list:")
debug(reconstructed_plane)
