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


def test_crc32_is_canonical_ieee():
    # SGEO uses the canonical IEEE-802.3 reflected polynomial 0xEDB88320, so
    # sgeo.crc32 must match a bit-by-bit reference using that polynomial.
    samples = [
        b"",
        b"SGEO",
        b"the quick brown fox",
        bytes(range(256)),
        b"\x00\x01\x02\x03\xff\xfe\xfd",
    ]
    for s in samples:
        assert sgeo.crc32(s) == _reference_crc32(s, 0xEDB88320)


def test_crc32_equals_zlib():
    # SGEO's CRC is standard CRC-32, so it equals zlib.crc32 (which is how the
    # encoder computes it — a C-speed call rather than a Python byte loop).
    import zlib

    for s in (b"", b"the quick brown fox", bytes(range(256))):
        assert sgeo.crc32(s) == (zlib.crc32(s) & 0xFFFFFFFF)


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


# ── decoding ───────────────────────────────────────────────────────────────


def test_decode_header_roundtrips_metadata():
    header = sgeo.decode_header(sgeo.encode(_make_mesh(units="mm")))
    assert header.version == sgeo.VERSION_1
    assert header.primitive is sgeo.PrimitiveType.MESH
    assert header.units_code == 1
    assert header.units == "mm"
    assert header.flags == sgeo.Flags.NONE


def test_get_unit_from_encoding_inverts_the_encoder():
    for unit in ("mm", "cm", "m", "km", "in", "ft", "yd", "mi"):
        assert sgeo.get_unit_from_encoding(sgeo.get_encoding_from_unit(unit)) == unit
    # 0 is the catch-all the encoder maps every unrecognised string to, so it
    # cannot decode back to a specific unit.
    assert sgeo.get_unit_from_encoding(0) is None


def test_decode_mesh_roundtrip_minimal():
    mesh = _make_mesh()
    decoded = sgeo.decode_mesh(sgeo.encode(mesh))
    assert decoded.vertices == mesh.vertices
    assert decoded.faces == mesh.faces
    assert decoded.units == "m"
    assert decoded.vertex_normals == []
    assert decoded.texture_coordinates == []
    assert decoded.colors == []


def test_decode_mesh_roundtrip_normals_and_colors():
    # The aligned case: 3 vertices + 4 faces leaves the body 8-aligned, so the
    # pad before normals is a no-op and colours follow with no pad at all.
    colors = [-1, -16711936, 255]
    mesh = _make_mesh(vertexNormals=[0.0, 0.0, 1.0] * 3, colors=colors)
    decoded = sgeo.decode_mesh(sgeo.encode(mesh))
    assert decoded.vertex_normals == [0.0, 0.0, 1.0] * 3
    # signed on the way out, matching Mesh.colors' signed ARGB ints
    assert decoded.colors == colors


def test_decode_mesh_roundtrip_skips_pad_before_normals():
    # 5 face ints leave the body at 4 mod 8, so the decoder must skip the same
    # 4 pad bytes the encoder wrote or every normal reads shifted.
    mesh = _make_mesh(
        faces=[4, 0, 1, 2, 3],
        vertexNormals=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
    )
    decoded = sgeo.decode_mesh(sgeo.encode(mesh))
    assert decoded.faces == [4, 0, 1, 2, 3]
    assert decoded.vertex_normals == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]


def test_decode_mesh_roundtrip_all_optional_arrays():
    mesh = _make_mesh(
        faces=[4, 0, 1, 2, 3],
        vertexNormals=[1.0] * 9,
        textureCoordinates=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
        colors=[7, 8, 9],
    )
    decoded = sgeo.decode_mesh(sgeo.encode(mesh))
    assert decoded.vertex_normals == [1.0] * 9
    assert decoded.texture_coordinates == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    assert decoded.colors == [7, 8, 9]


def test_decode_mesh_roundtrip_uvs_without_normals():
    # UVs carry their own pad, independent of whether normals were written.
    mesh = _make_mesh(
        faces=[4, 0, 1, 2, 3], textureCoordinates=[0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    )
    decoded = sgeo.decode_mesh(sgeo.encode(mesh))
    assert decoded.texture_coordinates == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    assert decoded.vertex_normals == []


def test_decode_returns_a_mesh():
    decoded = sgeo.decode(sgeo.encode(_make_mesh(units="ft")))
    assert isinstance(decoded, Mesh)
    assert decoded.units == "ft"
    assert decoded.faces == [3, 0, 1, 2]
    assert decoded.vertices == [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0]


def test_decode_rejects_corrupt_body():
    blob = bytearray(sgeo.encode(_make_mesh()))
    blob[sgeo.HEADER_SIZE + 8] ^= 0xFF  # flip a bit inside the first vertex
    with pytest.raises(sgeo.SgeoDecodeError, match="CRC mismatch"):
        sgeo.decode_mesh(bytes(blob))


def test_decode_skips_crc_when_asked():
    blob = bytearray(sgeo.encode(_make_mesh()))
    blob[sgeo.HEADER_SIZE + 8] ^= 0xFF
    # verify=False is for callers that already checksummed the transport
    sgeo.decode_mesh(bytes(blob), verify=False)


def test_decode_rejects_bad_magic():
    with pytest.raises(sgeo.SgeoDecodeError, match="magic"):
        sgeo.decode_header(b"NOPE" + bytes(12))


def test_decode_rejects_short_blob():
    with pytest.raises(sgeo.SgeoDecodeError, match="shorter than"):
        sgeo.decode_header(b"SGEO")


def test_decode_rejects_unsupported_version():
    blob = bytearray(sgeo.encode(_make_mesh()))
    blob[4] = 2
    with pytest.raises(sgeo.SgeoDecodeError, match="version"):
        sgeo.decode_header(bytes(blob))


def test_decode_rejects_truncated_body():
    blob = sgeo.encode(_make_mesh())
    with pytest.raises(sgeo.SgeoDecodeError, match="truncated"):
        # verify=False so we hit the length check, not the CRC
        sgeo.decode_mesh(blob[:-8], verify=False)


def test_decode_non_mesh_primitive_is_explicit():
    # Not-yet-implemented must be distinguishable from no-geometry, so the
    # other primitives raise rather than returning None.
    from specklepy.objects.geometry.line import Line
    from specklepy.objects.geometry.point import Point

    line = Line(
        start=Point(x=0, y=0, z=0, units="m"),
        end=Point(x=1, y=1, z=1, units="m"),
        units="m",
    )
    with pytest.raises(sgeo.SgeoDecodeError, match="LINE"):
        sgeo.decode(sgeo.encode(line))
    with pytest.raises(sgeo.SgeoDecodeError, match="LINE"):
        sgeo.decode_mesh(sgeo.encode(line))
