from collections import defaultdict
from collections.abc import Sequence
from typing import cast

from ifcopenshell.ifcopenshell_wrapper import (
    Triangulation,
    TriangulationElement,
    colour,
    style,
)
from specklepy.objects.base import Base
from specklepy.objects.geometry import Mesh
from specklepy.objects.other import RenderMaterial

from speckleifc.render_material_proxy_manager import RenderMaterialProxyManager


def geometry_to_speckle(
    shape: TriangulationElement, render_material_manager: RenderMaterialProxyManager
) -> list[Base]:
    geometry = cast(Triangulation, shape.geometry)
    materials = cast(Sequence[style], geometry.materials)
    MESH_COUNT = max(len(materials), 1)

    material_ids = cast(Sequence[int], geometry.material_ids)
    faces = cast(Sequence[int], geometry.faces)
    verts = cast(Sequence[float], geometry.verts)
    normals = cast(Sequence[float], geometry.normals)

    FACE_COUNT = len(material_ids)

    if len(faces) != FACE_COUNT * 3:
        # Not really expected, but occasionally some meshes fail to triangulate
        return []

    mapped_meshes = _pre_alloc_mesh_lists(shape, material_ids, MESH_COUNT)
    for i, mesh in enumerate(mapped_meshes):
        material = _material_to_speckle(materials[i])
        render_material_manager.add_mesh_material_mapping(material, mesh)

    mapped_faces_pointers = [0] * MESH_COUNT
    mapped_vertices_pointers = [0] * MESH_COUNT
    mapped_index_counters = [0] * MESH_COUNT

    i = 0
    face_index = 0
    while i < FACE_COUNT:
        mesh_index = material_ids[i]
        mesh: Mesh = mapped_meshes[mesh_index]

        face_ptr = mapped_faces_pointers[mesh_index]
        vert_ptr = mapped_vertices_pointers[mesh_index]

        # Add triangle
        mesh.faces[face_ptr] = 3
        for j in range(3):
            # Add vert
            mesh.faces[face_ptr + 1 + j] = mapped_index_counters[mesh_index] + j
            vert_index = faces[face_index + j] * 3
            mapped_vert_offset = vert_ptr + (j * 3)

            mesh.vertices[mapped_vert_offset] = verts[vert_index]
            mesh.vertices[mapped_vert_offset + 1] = verts[vert_index + 1]
            mesh.vertices[mapped_vert_offset + 2] = verts[vert_index + 2]

            mesh.vertexNormals[mapped_vert_offset] = normals[vert_index]
            mesh.vertexNormals[mapped_vert_offset + 1] = normals[vert_index + 1]
            mesh.vertexNormals[mapped_vert_offset + 2] = normals[vert_index + 2]

        i += 1
        face_index += 3  # number of items in the faces list we just jumped over

        mapped_index_counters[
            mesh_index
        ] += 3  # number of verts we just added to the mesh.vertices i.e. the next index
        mapped_faces_pointers[
            mesh_index
        ] += 4  # number of item's we've just added to the mesh.faces list
        mapped_vertices_pointers[
            mesh_index
        ] += 9  # number of item's we've just added to the mesh.vertices list

    return mapped_meshes  # type: ignore


def _material_to_speckle(material: style) -> RenderMaterial:
    return RenderMaterial(
        applicationId=material.calc_hash(),
        name=material.name,
        diffuse=_color_to_argb(material.diffuse),
        opacity=1 - material.transparency if material.has_transparency() else 1,
    )


def _color_to_argb(colour: colour) -> int:
    # Clamp values to [0, 1] and convert to 0–255
    a_int = 255
    r_int = max(0, min(255, int(round(colour.r() * 255))))
    g_int = max(0, min(255, int(round(colour.g() * 255))))
    b_int = max(0, min(255, int(round(colour.b() * 255))))

    return (a_int << 24) | (r_int << 16) | (g_int << 8) | b_int


def _pre_alloc_mesh_lists(
    shape: TriangulationElement, material_ids: Sequence[int], MESH_COUNT: int
) -> list[Mesh]:
    """
    This is a performance optimisation to pre-size the lists
    since we're expecting potential hundreds of thousands of verts in a single model
    This is very much in the hot path, so worth the extra bit of convoluted logic
    """
    appId = cast(str, shape.guid)

    material_face_counts = defaultdict(int)
    for mat_id in material_ids:
        material_face_counts[mat_id] += 1

    meshes = []
    for mat_id in range(MESH_COUNT):
        face_count = material_face_counts.get(mat_id, 0)
        mesh = Mesh(
            units="m",
            vertices=[-1] * (face_count * 9),
            vertexNormals=[-1] * (face_count * 9),
            faces=[-1] * (face_count * 4),  # 1 marker + 3 vertex indices
            applicationId=f"{appId}_mat{mat_id}",
        )
        meshes.append(mesh)
    return meshes
