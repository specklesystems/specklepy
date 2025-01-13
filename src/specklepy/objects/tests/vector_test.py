from devtools import debug

from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry import Vector
from specklepy.objects.other import Transform
from specklepy.objects.models.units import Units

# Create test vectors
v1 = Vector(x=1.0, y=2.0, z=3.0, units=Units.m)
v2 = Vector(x=4.0, y=5.0, z=6.0, units=Units.m, applicationId="test_vector")

print("\nVector 1:")
debug(v1)
print(f"Length: {v1.length}")

print("\nVector 2:")
debug(v2)
print(f"Length: {v2.length}")

# Test serialization
ser_vector = serialize(v1)
vector_again = deserialize(ser_vector)

print("\nOriginal vector:")
debug(v1)
print("\nSerialized vector:")
debug(ser_vector)
print("\nDeserialized vector:")
debug(vector_again)

# Test transform
# Create a transform matrix that scales by 2 in x direction, 3 in y, and 4 in z
# and translates by (1,2,3)
transform_matrix = [
    2.0, 0.0, 0.0, 1.0,  # Scale x by 2, translate x by 1
    0.0, 3.0, 0.0, 2.0,  # Scale y by 3, translate y by 2
    0.0, 0.0, 4.0, 3.0,  # Scale z by 4, translate z by 3
    0.0, 0.0, 0.0, 1.0
]

transform = Transform(matrix=transform_matrix, units=Units.m)

print("\nTransform matrix:")
debug(transform)

# Test vector transformation
success, transformed_vector = v1.transform_to(transform)

print("\nOriginal vector:")
debug(v1)
print("\nTransformed vector:")
debug(transformed_vector)

# Test unit conversion
transform_mm = Transform(matrix=transform_matrix, units="mm")
mm_matrix = transform_mm.convert_to_units("m")

print("\nTransform matrix in millimeters converted to meters:")
debug(mm_matrix)

# Test matrix creation
custom_matrix = Transform.create_matrix([
    1.0, 0.0, 0.0, 5.0,
    0.0, 1.0, 0.0, 5.0,
    0.0, 0.0, 1.0, 5.0,
    0.0, 0.0, 0.0, 1.0
])

custom_transform = Transform(matrix=custom_matrix, units=Units.m)
print("\nCustom transform matrix:")
debug(custom_transform)

# Test serialization of transform
ser_transform = serialize(transform)
transform_again = deserialize(ser_transform)

print("\nOriginal transform:")
debug(transform)
print("\nSerialized transform:")
debug(ser_transform)
print("\nDeserialized transform:")
debug(transform_again)
