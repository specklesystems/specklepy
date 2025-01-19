from devtools import debug
from specklepy.core.api.operations import deserialize, serialize
from specklepy.objects.geometry import Mesh

# create a speckle cube mesh (but more colorful)
vertices = [
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    1.0,
    1.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    1.0,
    1.0,
    0.0,
    1.0,
    1.0,
    1.0,
    1.0,
    0.0,
    1.0,
    1.0,
]

# define faces (triangles)
faces = [
    3,
    0,
    1,
    2,
    3,
    0,
    2,
    3,
    3,
    4,
    5,
    6,
    3,
    4,
    6,
    7,
    3,
    0,
    4,
    7,
    3,
    0,
    7,
    3,
    3,
    1,
    5,
    6,
    3,
    1,
    6,
    2,
    3,
    3,
    2,
    6,
    3,
    3,
    6,
    7,
    3,
    0,
    1,
    5,
    3,
    0,
    5,
    4,
]

# create colors (one per vertex)
colors = [
    255,
    0,
    0,
    255,
    0,
    255,
    0,
    255,
    0,
    0,
    255,
    255,
    255,
    255,
    0,
    255,
    255,
    0,
    255,
    255,
    0,
    255,
    255,
    255,
    255,
    255,
    255,
    255,
    0,
    0,
    0,
    255,
]

texture_coordinates = [
    0.0,
    0.0,
    1.0,
    0.0,
    1.0,
    1.0,
    0.0,
    1.0,
    0.0,
    0.0,
    1.0,
    0.0,
    1.0,
    1.0,
    0.0,
    1.0,
]

# create the mesh
cube_mesh = Mesh(
    vertices=vertices,
    faces=faces,
    colors=colors,
    textureCoordinates=texture_coordinates,
    units="mm",
    area=0.0,
    volume=0.0,
)

print(f"\nMesh Details:")
print(f"Number of vertices: {cube_mesh.vertices_count}")
print(f"Number of texture coordinates: {cube_mesh.texture_coordinates_count}")

print("\nSome vertex points:")
for i in range(4):
    point = cube_mesh.get_point(i)
    print(f"Vertex {i}: ({point.x}, {point.y}, {point.z})")

print("\nSome texture coordinates:")
for i in range(4):
    u, v = cube_mesh.get_texture_coordinate(i)
    print(f"Texture coordinate {i}: ({u}, {v})")

print("\nTesting serialization...")
ser_mesh = serialize(cube_mesh)
mesh_again = deserialize(ser_mesh)

print("\nOriginal mesh:")
debug(cube_mesh)
print("\nDeserialized mesh:")
debug(mesh_again)

print("\nTesting vertex-texture coordinate alignment...")
cube_mesh.align_vertices_with_texcoords_by_index()
print("Alignment complete.")

print(f"Vertices count after alignment: {cube_mesh.vertices_count}")
print(
    f"Texture coordinates count after alignment: {cube_mesh.texture_coordinates_count}"
)
