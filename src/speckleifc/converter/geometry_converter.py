from collections.abc import Sequence
from typing import cast

from ifcopenshell import file
from ifcopenshell.ifcopenshell_wrapper import Triangulation
from specklepy.objects import Base
from specklepy.objects.geometry import Mesh


def geometry_to_speckle(geometry: Triangulation, ifc_model: file) -> list[Base]:

    materials = cast(Sequence[int], geometry.materials)
    MESH_COUNT = max(len(materials), 1)

    meshes: list[Mesh] = [
        Mesh(units="m", vertices=[], faces=[]) for i in range(MESH_COUNT)
    ]
    index_counters = [0] * MESH_COUNT

    faces = cast(Sequence[int], geometry.faces)
    verts = cast(Sequence[float], geometry.verts)
    normals = cast(Sequence[float], geometry.normals)
    uvs = cast(Sequence[float], geometry.uvs)

    material_ids = cast(Sequence[int], geometry.material_ids)

    FACE_COUNT = len(material_ids)

    assert len(faces) == FACE_COUNT * 3
    # assert len(normals) == len(verts)
    # assert len(uvs) == len(verts) ||

    i = 0
    face_index = 0
    while i < FACE_COUNT:
        mesh: Mesh = meshes[material_ids[i]]

        # Add triangle
        mesh.faces.append(3)

        mesh.faces.append(index_counters[material_ids[i]])
        mesh.vertices.append(verts[faces[face_index] * 3])
        mesh.vertices.append(verts[faces[face_index] * 3 + 1])
        mesh.vertices.append(verts[faces[face_index] * 3 + 2])

        mesh.faces.append(index_counters[material_ids[i]] + 1)
        mesh.vertices.append(verts[faces[face_index + 1] * 3])
        mesh.vertices.append(verts[faces[face_index + 1] * 3 + 1])
        mesh.vertices.append(verts[faces[face_index + 1] * 3 + 2])

        mesh.faces.append(index_counters[material_ids[i]] + 2)
        mesh.vertices.append(verts[faces[face_index + 2] * 3])
        mesh.vertices.append(verts[faces[face_index + 2] * 3 + 1])
        mesh.vertices.append(verts[faces[face_index + 2] * 3 + 2])

        # Add normals
        if len(normals) > 0:
            mesh.vertexNormals.append(normals[faces[face_index] * 3])
            mesh.vertexNormals.append(normals[faces[face_index] * 3 + 1])
            mesh.vertexNormals.append(normals[faces[face_index] * 3 + 2])

            mesh.vertexNormals.append(normals[faces[face_index + 1] * 3])
            mesh.vertexNormals.append(normals[faces[face_index + 1] * 3 + 1])
            mesh.vertexNormals.append(normals[faces[face_index + 1] * 3 + 2])

            mesh.vertexNormals.append(normals[faces[face_index + 2] * 3])
            mesh.vertexNormals.append(normals[faces[face_index + 2] * 3 + 1])
            mesh.vertexNormals.append(normals[faces[face_index + 2] * 3 + 2])

        # Add uvs
        if len(uvs) > 0:
            mesh.textureCoordinates.append(uvs[faces[face_index] * 3])
            mesh.textureCoordinates.append(uvs[faces[face_index] * 3 + 1])

            mesh.textureCoordinates.append(uvs[faces[face_index + 1] * 3])
            mesh.textureCoordinates.append(uvs[faces[face_index + 1] * 3 + 1])

            mesh.textureCoordinates.append(uvs[faces[face_index + 2] * 3])
            mesh.textureCoordinates.append(uvs[faces[face_index + 2] * 3 + 1])

        index_counters[material_ids[i]] += 3
        i += 1
        face_index += 3

    return meshes  # type: ignore
