import struct

import pytest

from specklepy.bundle import sgeo
from specklepy.objects.geometry.mesh import Mesh


def _make_mesh(**kwargs) -> Mesh:
    defaults = dict(
        vertices=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        faces=[3, 0, 1, 2],
        units="m",
    )
    defaults.update(kwargs)
    return Mesh(**defaults)


def _reference_crc32(data: bytes, poly: int) -> int:
    """Independent table-free CRC32 reference, parameterised by polynomial."""
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (poly ^ (crc >> 1)) if (crc & 1) else (crc >> 1)
    return crc ^ 0xFFFFFFFF


def test_crc32_matches_dotnet_polynomial():
    # SgeoFormat.cs uses the constant 0xEDB88820 (NOT the canonical IEEE
    # 0xEDB88320). We replicate it for byte-for-byte parity with the .NET
    # encoder, so sgeo.crc32 must match a bit-by-bit reference using 0xEDB88820.
    samples = [
        b"",
        b"SGEO",
        b"the quick brown fox",
        bytes(range(256)),
        b"\x00\x01\x02\x03\xff\xfe\xfd",
    ]
    for s in samples:
        assert sgeo.crc32(s) == _reference_crc32(s, 0xEDB88820)


def test_crc32_differs_from_zlib_due_to_nonstandard_poly():
    # Document the gotcha: SGEO's CRC is NOT standard CRC-32, so it must not be
    # swapped for zlib.crc32. zlib equals the canonical 0xEDB88320 reference.
    import zlib

    s = b"the quick brown fox"
    assert sgeo.crc32(s) == _reference_crc32(s, 0xEDB88820)
    assert (zlib.crc32(s) & 0xFFFFFFFF) == _reference_crc32(s, 0xEDB88320)
    assert sgeo.crc32(s) != (zlib.crc32(s) & 0xFFFFFFFF)


def test_unit_encoding_mapping():
    assert sgeo.get_encoding_from_unit("mm") == 1
    assert sgeo.get_encoding_from_unit("cm") == 2
    assert sgeo.get_encoding_from_unit("m") == 3
    assert sgeo.get_encoding_from_unit("km") == 4
    assert sgeo.get_encoding_from_unit("in") == 5
    assert sgeo.get_encoding_from_unit("ft") == 6
    assert sgeo.get_encoding_from_unit("yd") == 7
    assert sgeo.get_encoding_from_unit("mi") == 8
    # unknown / aliases / none silently map to 0 (matches C# GetEncodingFromUnit)
    assert sgeo.get_encoding_from_unit("none") == 0
    assert sgeo.get_encoding_from_unit("millimeters") == 0
    assert sgeo.get_encoding_from_unit(None) == 0


def test_try_get_primitive_type():
    assert sgeo.try_get_primitive_type(_make_mesh()) == 0
    assert sgeo.try_get_primitive_type(object()) is None


def test_mesh_header_bytes():
    mesh = _make_mesh(units="mm")
    blob = sgeo.encode(mesh)

    # magic, version, primitive type
    assert blob[0:4] == b"SGEO"
    assert blob[4] == sgeo.VERSION_1 == 1
    assert blob[5] == int(sgeo.PrimitiveType.MESH) == 0

    # flags (no normals/uvs/colors) == 0
    flags = struct.unpack_from("<H", blob, 6)[0]
    assert flags == 0

    # units code for "mm" == 1
    units_code = struct.unpack_from("<H", blob, 8)[0]
    assert units_code == 1

    # reserved == 0
    assert struct.unpack_from("<H", blob, 10)[0] == 0

    # body starts at 0x10, header is 16 bytes
    assert sgeo.HEADER_SIZE == 16
    body = blob[sgeo.HEADER_SIZE :]

    # crc matches recomputation over the body bytes only
    stored_crc = struct.unpack_from("<I", blob, 12)[0]
    assert stored_crc == sgeo.crc32(body)


def test_mesh_body_layout():
    vertices = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    faces = [3, 0, 1, 2]
    mesh = _make_mesh(vertices=vertices, faces=faces, units="m")
    blob = sgeo.encode(mesh)
    body = blob[sgeo.HEADER_SIZE :]

    vertex_count = struct.unpack_from("<I", body, 0)[0]
    face_count = struct.unpack_from("<I", body, 4)[0]
    assert vertex_count == len(vertices) // 3 == 3
    assert face_count == len(faces) == 4

    # first vertex triple starts at offset 8 (after the two uint32 counts)
    first_x = struct.unpack_from("<d", body, 8)[0]
    first_y = struct.unpack_from("<d", body, 16)[0]
    first_z = struct.unpack_from("<d", body, 24)[0]
    assert (first_x, first_y, first_z) == (0.0, 0.0, 0.0)

    # second vertex
    second_x = struct.unpack_from("<d", body, 32)[0]
    assert second_x == 1.0

    # faces follow all vertices: 9 doubles = 72 bytes, +8 header = offset 80
    faces_offset = 8 + len(vertices) * 8
    decoded_faces = [
        struct.unpack_from("<i", body, faces_offset + i * 4)[0]
        for i in range(len(faces))
    ]
    assert decoded_faces == faces

    # exact total length: header + counts + vertices + faces, no trailing pad
    expected_len = sgeo.HEADER_SIZE + 8 + len(vertices) * 8 + len(faces) * 4
    assert len(blob) == expected_len


def test_mesh_with_normals_and_colors_flags_and_pad():
    vertices = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    faces = [3, 0, 1, 2]
    normals = [0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0]
    colors = [-1, -16711936, 255]  # signed ARGB-style ints
    mesh = _make_mesh(
        vertices=vertices,
        faces=faces,
        vertexNormals=normals,
        colors=colors,
        units="m",
    )
    blob = sgeo.encode(mesh)

    flags = struct.unpack_from("<H", blob, 6)[0]
    assert flags & int(sgeo.Flags.HAS_NORMALS)
    assert flags & int(sgeo.Flags.HAS_COLORS)
    assert not (flags & int(sgeo.Flags.HAS_UVS))
    assert int(sgeo.Flags.HAS_NORMALS) == 1 << 4
    assert int(sgeo.Flags.HAS_COLORS) == 1 << 6

    body = blob[sgeo.HEADER_SIZE :]

    # vertices(9) + faces(4): 8 + 72 + 16 = 96 bytes -> already 8-aligned,
    # so Pad8 before normals adds nothing here.
    normals_offset = 8 + len(vertices) * 8 + len(faces) * 4
    assert normals_offset % 8 == 0
    n0 = struct.unpack_from("<d", body, normals_offset + 2 * 8)[0]
    assert n0 == 1.0  # third component of first normal

    # colors directly follow the normals (NO pad before colors)
    colors_offset = normals_offset + len(normals) * 8
    decoded_colors = [
        struct.unpack_from("<i", body, colors_offset + i * 4)[0]
        for i in range(len(colors))
    ]
    assert decoded_colors == colors

    # crc still valid
    stored_crc = struct.unpack_from("<I", blob, 12)[0]
    assert stored_crc == sgeo.crc32(body)


def test_pad8_alignment_when_faces_misaligned():
    # 3 vertices + 5 faces: 8 + 72 + 20 = 100 bytes body before normals.
    # 100 % 8 == 4, so Pad8 must add 4 bytes before the normals f64 block.
    vertices = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    faces = [4, 0, 1, 2, 3]  # 5 ints
    normals = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
    mesh = _make_mesh(vertices=vertices, faces=faces, vertexNormals=normals, units="m")
    blob = sgeo.encode(mesh)
    body = blob[sgeo.HEADER_SIZE :]

    pre_pad = 8 + len(vertices) * 8 + len(faces) * 4
    assert pre_pad % 8 == 4
    padded = pre_pad + 4
    assert padded % 8 == 0
    # padding bytes are zero
    assert body[pre_pad:padded] == b"\x00\x00\x00\x00"
    first_normal = struct.unpack_from("<d", body, padded)[0]
    assert first_normal == 1.0


def test_encode_unknown_raises():
    with pytest.raises(ValueError):
        sgeo.encode(object())
