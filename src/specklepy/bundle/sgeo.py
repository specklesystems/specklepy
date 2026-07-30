"""SGEO v1 geometry codec — a byte-for-byte port of the .NET ``SgeoEncoder``.

SGEO is Speckle's binary geometry-family format: one opaque blob per geometry
buffer, a fixed 16-byte little-endian header followed by a per-primitive body.
The SDK owns the format; this module mirrors the C# encoder in
``Speckle.Objects/Utils/SgeoEncoder.cs`` exactly so that connectors written in
Python produce identical bytes.

Header (16 bytes, little-endian)::

    0x00  4  magic           b"SGEO"
    0x04  1  version         = 1
    0x05  1  primitive_type  see PrimitiveType
    0x06  2  flags           uint16 (see Flags)
    0x08  2  units_code      uint16, mirrors Units.GetEncodingFromUnit
    0x0A  2  reserved        = 0
    0x0C  4  crc             CRC32 of body bytes only (0x10..end)
    0x10  …  body            per primitive_type

Conventions: little-endian throughout; f64 = IEEE-754 double; the body starts
8-byte aligned at 0x10 and every f64 array stays 8-aligned (u32 scalars are
padded in pairs via :func:`_pad8`).

:func:`encode` writes blobs; :func:`decode` reads them back for the receive side
of the artefact path, covering every primitive the encoder emits.
:func:`decode_mesh` is a raw-array fast path for MESH only — meshes are the
dense case where allocating a ``Base`` per geometry dominates, and connectors
that bake straight into a host application want the flat arrays anyway.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from enum import IntEnum, IntFlag
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from specklepy.objects.base import Base

MAGIC = b"SGEO"
VERSION_1 = 1
HEADER_SIZE = 16
ENCODING_NAME = "sgeo_v1"


class PrimitiveType(IntEnum):
    """SGEO primitive type codes (header offset 0x05, one byte)."""

    MESH = 0
    LINE = 1
    POLYLINE = 2
    POLYCURVE = 3
    CURVE = 4
    ARC = 5
    CIRCLE = 6
    POINTS = 7
    ELLIPSE = 8
    SPIRAL = 9
    BOX = 10


class Flags(IntFlag):
    """SGEO header flags (offset 0x06, uint16 bitfield)."""

    NONE = 0
    QUANTIZED = 1 << 0
    CLOSED = 1 << 1
    RATIONAL = 1 << 2
    PERIODIC = 1 << 3
    HAS_NORMALS = 1 << 4
    HAS_UVS = 1 << 5
    HAS_COLORS = 1 << 6
    HAS_SIZES = 1 << 7
    HAS_TRIM_DOMAIN = 1 << 8


# Mirrors Speckle.Sdk.Common.Units.GetEncodingFromUnit: the exact semantic unit
# strings map to 1..8, anything else (aliases, unknown, none) silently maps to 0.
_UNIT_ENCODING = {
    "mm": 1,
    "cm": 2,
    "m": 3,
    "km": 4,
    "in": 5,
    "ft": 6,
    "yd": 7,
    "mi": 8,
}


def get_encoding_from_unit(units: Optional[str]) -> int:
    """Map a semantic unit string to its SGEO uint16 code (0 if unrecognised)."""
    return _UNIT_ENCODING.get(units or "", 0)


# ── CRC32 (IEEE 802.3, polynomial 0xEDB88820) ──────────────────────────────


def crc32(data: bytes) -> int:
    """SGEO body CRC — canonical CRC-32 (IEEE 802.3, reflected poly ``0xEDB88320``).

    This is exactly what :func:`zlib.crc32` computes (init/final ``0xFFFFFFFF``,
    reflected), so we delegate to it — a C-speed call instead of a per-byte Python
    loop, which was the dominant cost when writing dense-mesh bundles. The whole
    stack (this encoder, the .NET ``SgeoEncoder``, the native nw/rvextract writers)
    uses the standard polynomial so blobs stay byte-for-byte identical across
    producers (content-hash dedup hashes the whole blob, header included).
    """
    return zlib.crc32(data) & 0xFFFFFFFF


# ── low-level body writers ─────────────────────────────────────────────────


def _f64(b: bytearray, v: float) -> None:
    b += struct.pack("<d", v)


def _i32(b: bytearray, v: int) -> None:
    # Low 32 bits, matching C# AddInt32's (byte)(v >> 8*i) over a 32-bit int.
    b += struct.pack("<I", v & 0xFFFFFFFF)


def _f64_array(b: bytearray, vals) -> None:
    """Pack a whole float sequence as little-endian f64 in one struct call."""
    if vals:
        b += struct.pack(f"<{len(vals)}d", *vals)


def _i32_array(b: bytearray, vals) -> None:
    """Pack a whole int sequence as low-32-bit LE words in one struct call.

    Masked to 32 bits (unsigned ``I``) so packed ARGB colours (> int32 max) and mesh
    face indices share one path, matching ``_i32``'s ``& 0xFFFFFFFF`` byte layout.
    """
    if vals:
        b += struct.pack(f"<{len(vals)}I", *[v & 0xFFFFFFFF for v in vals])


def _u32(b: bytearray, v: int) -> None:
    b += struct.pack("<I", v & 0xFFFFFFFF)


def _pad8(b: bytearray) -> None:
    while len(b) % 8 != 0:
        b.append(0)


def _point(b: bytearray, p) -> None:
    _f64(b, p.x)
    _f64(b, p.y)
    _f64(b, p.z)


def _vector(b: bytearray, v) -> None:
    _f64(b, v.x)
    _f64(b, v.y)
    _f64(b, v.z)


def _plane(b: bytearray, p) -> None:
    _point(b, p.origin)
    _vector(b, p.normal)
    _vector(b, p.xdir)
    _vector(b, p.ydir)


def _polyline_body(b: bytearray, p) -> None:
    # Shared by EncodePolyline and the curve/spiral leading render polyline.
    if len(p.value) % 3 != 0:
        raise ValueError("Polyline.value length must be a multiple of 3.")
    _u32(b, len(p.value) // 3)
    _u32(b, 0)
    for v in p.value:
        _f64(b, v)
    _pad8(b)


def _assemble(
    primitive_type: PrimitiveType, flags: Flags, units: Optional[str], body: bytearray
) -> bytes:
    buf = bytearray(HEADER_SIZE + len(body))
    buf[0:4] = MAGIC  # 0x00..0x03
    buf[4] = VERSION_1  # 0x04
    buf[5] = int(primitive_type)  # 0x05
    struct.pack_into("<H", buf, 6, int(flags))  # 0x06 flags
    struct.pack_into("<H", buf, 8, get_encoding_from_unit(units))  # 0x08 units
    struct.pack_into("<H", buf, 10, 0)  # 0x0A reserved
    buf[HEADER_SIZE:] = body
    # Must use the ported crc32 (poly 0xEDB88820), NOT zlib — see crc32 docstring.
    crc = crc32(bytes(body))
    struct.pack_into("<I", buf, 12, crc)  # 0x0C crc
    return bytes(buf)


# ── per-primitive encoders ─────────────────────────────────────────────────


def _encode_mesh(m) -> bytes:
    if len(m.vertices) % 3 != 0:
        raise ValueError("Mesh.vertices length must be a multiple of 3.")
    has_normals = len(m.vertexNormals) > 0
    has_uvs = len(m.textureCoordinates) > 0
    has_colors = len(m.colors) > 0

    flags = Flags.NONE
    if has_normals:
        flags |= Flags.HAS_NORMALS
    if has_uvs:
        flags |= Flags.HAS_UVS
    if has_colors:
        flags |= Flags.HAS_COLORS

    body = bytearray()
    _u32(body, len(m.vertices) // 3)
    _u32(body, len(m.faces))
    # Batched packs: one struct.pack per array (C-level) instead of one call per
    # scalar — the per-double/-int loop was a hot spot on dense meshes. Byte layout
    # is unchanged.
    _f64_array(body, m.vertices)
    _i32_array(body, m.faces)
    if has_normals:
        _pad8(body)
        _f64_array(body, m.vertexNormals)
    if has_uvs:
        _pad8(body)
        _f64_array(body, m.textureCoordinates)
    if has_colors:
        # NB: no pad before colors — matches the C# encoder exactly.
        _i32_array(body, m.colors)

    return _assemble(PrimitiveType.MESH, flags, m.units, body)


def _encode_line(line) -> bytes:
    body = bytearray()
    _f64(body, line.domain.start)
    _f64(body, line.domain.end)
    _point(body, line.start)
    _point(body, line.end)
    return _assemble(PrimitiveType.LINE, Flags.NONE, line.units, body)


def _encode_polyline(p) -> bytes:
    if len(p.value) % 3 != 0:
        raise ValueError("Polyline.value length must be a multiple of 3.")
    flags = Flags.CLOSED if _is_closed(p) else Flags.NONE
    body = bytearray()
    _u32(body, len(p.value) // 3)
    _u32(body, 0)
    for v in p.value:
        _f64(body, v)
    return _assemble(PrimitiveType.POLYLINE, flags, p.units, body)


def _encode_polycurve(pc) -> bytes:
    flags = Flags.CLOSED if _is_closed(pc) else Flags.NONE
    body = bytearray()
    _u32(body, len(pc.segments))
    _u32(body, 0)
    for seg in pc.segments:
        blob = encode(seg)
        _u32(body, len(blob))
        _u32(body, 0)
        body += blob
        _pad8(body)
    return _assemble(PrimitiveType.POLYCURVE, flags, pc.units, body)


def _encode_curve(c) -> bytes:
    if len(c.points) % 3 != 0:
        raise ValueError("Curve.points length must be a multiple of 3.")
    flags = Flags.NONE
    if _is_closed(c.displayValue):
        flags |= Flags.CLOSED
    if c.rational:
        flags |= Flags.RATIONAL
    if c.periodic:
        flags |= Flags.PERIODIC

    body = bytearray()
    _polyline_body(body, c.displayValue)  # [render] leading displayValue polyline
    _u32(body, c.degree)  # [analytical] trailing NURBS definition
    _u32(body, len(c.points) // 3)
    _u32(body, len(c.knots))
    _u32(body, 0)
    _f64(body, c.domain.start)
    _f64(body, c.domain.end)
    for p in c.points:
        _f64(body, p)
    if c.rational:
        for w in c.weights:
            _f64(body, w)
    for k in c.knots:
        _f64(body, k)
    return _assemble(PrimitiveType.CURVE, flags, c.units, body)


def _encode_arc(a) -> bytes:
    body = bytearray()
    _plane(body, a.plane)
    _point(body, a.startPoint)
    _point(body, a.midPoint)
    _point(body, a.endPoint)
    _f64(body, a.domain.start)
    _f64(body, a.domain.end)
    return _assemble(PrimitiveType.ARC, Flags.NONE, a.units, body)


def _encode_circle(c) -> bytes:
    body = bytearray()
    _f64(body, c.radius)
    _f64(body, c.domain.start)
    _f64(body, c.domain.end)
    _plane(body, c.plane)
    return _assemble(PrimitiveType.CIRCLE, Flags.NONE, c.units, body)


def _encode_point(pt) -> bytes:
    body = bytearray()
    _u32(body, 1)
    _u32(body, 0)
    _point(body, pt)
    return _assemble(PrimitiveType.POINTS, Flags.NONE, pt.units, body)


def _encode_pointcloud(pcl) -> bytes:
    # specklepy stores points as a list of Point objects (vs the C# flat double
    # list); flatten to x,y,z so the on-wire layout matches.
    points = pcl.points
    coords: list[float] = []
    for p in points:
        coords.extend((p.x, p.y, p.z))
    colors = list(getattr(pcl, "colors", []) or [])
    sizes = list(getattr(pcl, "sizes", []) or [])
    has_colors = len(colors) > 0
    has_sizes = len(sizes) > 0
    flags = Flags.NONE
    if has_colors:
        flags |= Flags.HAS_COLORS
    if has_sizes:
        flags |= Flags.HAS_SIZES

    body = bytearray()
    _u32(body, len(coords) // 3)
    _u32(body, 0)
    for v in coords:
        _f64(body, v)
    if has_colors:
        for c in colors:
            _i32(body, c)
    if has_sizes:
        _pad8(body)
        for s in sizes:
            _f64(body, s)
    return _assemble(PrimitiveType.POINTS, flags, pcl.units, body)


def _encode_ellipse(e) -> bytes:
    trim_domain = getattr(e, "trimDomain", None)
    flags = Flags.HAS_TRIM_DOMAIN if trim_domain is not None else Flags.NONE
    body = bytearray()
    _f64(body, e.first_radius)
    _f64(body, e.second_radius)
    _f64(body, e.domain.start)
    _f64(body, e.domain.end)
    _plane(body, e.plane)
    if trim_domain is not None:
        _f64(body, trim_domain.start)
        _f64(body, trim_domain.end)
    return _assemble(PrimitiveType.ELLIPSE, flags, e.units, body)


def _encode_spiral(s) -> bytes:
    display_value = getattr(s, "displayValue", None)
    is_closed = display_value is not None and _is_closed(display_value)
    flags = Flags.CLOSED if is_closed else Flags.NONE
    body = bytearray()
    if display_value is not None:  # [render] leading displayValue polyline
        _polyline_body(body, display_value)
    else:
        _u32(body, 0)
        _u32(body, 0)
        _pad8(body)
    _u32(body, int(getattr(s, "spiralType", 0)))  # [analytical] trailing definition
    _u32(body, 0)
    _point(body, s.start_point)
    _point(body, s.end_point)
    _plane(body, s.plane)
    _f64(body, s.turns)
    _vector(body, s.pitch_axis)
    _f64(body, s.pitch)
    _f64(body, s.domain.start)
    _f64(body, s.domain.end)
    return _assemble(PrimitiveType.SPIRAL, flags, s.units, body)


def _encode_box(b) -> bytes:
    body = bytearray()
    _plane(body, b.basePlane)
    _f64(body, b.xSize.start)
    _f64(body, b.xSize.end)
    _f64(body, b.ySize.start)
    _f64(body, b.ySize.end)
    _f64(body, b.zSize.start)
    _f64(body, b.zSize.end)
    return _assemble(PrimitiveType.BOX, Flags.NONE, b.units, body)


def _is_closed(curve) -> bool:
    closed = getattr(curve, "closed", None)
    if closed is not None:
        return bool(closed)
    is_closed = getattr(curve, "is_closed", None)
    if callable(is_closed):
        return bool(is_closed())
    return False


# ── public API ─────────────────────────────────────────────────────────────

# Lazy import map: speckle_type string -> encoder. Keyed by class name to avoid
# importing the whole geometry package at module load and to dodge cycles.
_ENCODERS = {
    "Mesh": _encode_mesh,
    "Line": _encode_line,
    "Polyline": _encode_polyline,
    "Polycurve": _encode_polycurve,
    "Curve": _encode_curve,
    "Arc": _encode_arc,
    "Circle": _encode_circle,
    "Point": _encode_point,
    "PointCloud": _encode_pointcloud,
    "Ellipse": _encode_ellipse,
    "Spiral": _encode_spiral,
    "Box": _encode_box,
}

_PRIMITIVE_TYPES = {
    "Mesh": PrimitiveType.MESH,
    "Line": PrimitiveType.LINE,
    "Polyline": PrimitiveType.POLYLINE,
    "Polycurve": PrimitiveType.POLYCURVE,
    "Curve": PrimitiveType.CURVE,
    "Arc": PrimitiveType.ARC,
    "Circle": PrimitiveType.CIRCLE,
    "Point": PrimitiveType.POINTS,
    "PointCloud": PrimitiveType.POINTS,
    "Ellipse": PrimitiveType.ELLIPSE,
    "Spiral": PrimitiveType.SPIRAL,
    "Box": PrimitiveType.BOX,
}


def encode(geometry) -> bytes:
    """Encode a supported geometry object into an SGEO v1 blob.

    Dispatches on the object's class name (mirroring ``SgeoEncoder.Encode``).

    Raises:
        ValueError: when the geometry type has no SGEO mapping.
    """
    if geometry is None:
        raise ValueError("Cannot encode None geometry.")
    encoder = _ENCODERS.get(type(geometry).__name__)
    if encoder is None:
        raise ValueError(
            f"No SGEO encoding for geometry type '{type(geometry).__name__}'."
        )
    return encoder(geometry)


def try_get_primitive_type(geometry) -> Optional[int]:
    """Return the SGEO primitive type code if encodable, else ``None``."""
    primitive = _PRIMITIVE_TYPES.get(type(geometry).__name__)
    return int(primitive) if primitive is not None else None


# ── decoding ───────────────────────────────────────────────────────────────
#
# The receive side of the artefact path: connectors that load a 4.0 bundle read
# geometry blobs back out of the geometries table. Every primitive the encoder
# emits can be decoded; unknown or corrupt blobs raise :class:`SgeoDecodeError`
# rather than silently returning nothing, so a caller can tell "not supported"
# from "no geometry".
#
# Two levels, deliberately: :func:`decode_mesh` returns a plain
# :class:`DecodedMesh` of raw arrays for consumers that bake straight into a
# host application (no Base allocation per mesh, which dominates on dense
# scenes), and :func:`decode` wraps that into a real ``Mesh`` for consumers
# that want the object model.


class SgeoDecodeError(ValueError):
    """A blob is not valid SGEO v1, or holds a primitive we cannot decode yet."""


_UNIT_DECODING = {code: unit for unit, code in _UNIT_ENCODING.items()}


def get_unit_from_encoding(code: int) -> Optional[str]:
    """Inverse of :func:`get_encoding_from_unit`; ``None`` for the 0 sentinel.

    Not round-trip-exact by construction: the encoder maps every unrecognised
    unit string to 0, so 0 decodes to ``None`` rather than to whatever the
    producer originally had.
    """
    return _UNIT_DECODING.get(code)


@dataclass(frozen=True)
class SgeoHeader:
    """The fixed 16-byte SGEO header, parsed."""

    version: int
    primitive_type: int
    flags: Flags
    units_code: int
    crc: int

    @property
    def units(self) -> Optional[str]:
        return get_unit_from_encoding(self.units_code)

    @property
    def primitive(self) -> Optional[PrimitiveType]:
        """The primitive as an enum member, or ``None`` for an unknown code."""
        try:
            return PrimitiveType(self.primitive_type)
        except ValueError:
            return None


@dataclass
class DecodedMesh:
    """A mesh's raw SGEO arrays, in Speckle's flat layout.

    ``faces`` is the flat ``[n, i0..in-1, n, i0..]`` face list, matching
    ``Mesh.faces``; ``vertices``/``vertexNormals`` are flat xyz triples and
    ``textureCoordinates`` flat uv pairs.
    """

    vertices: List[float]
    faces: List[int]
    vertex_normals: List[float]
    texture_coordinates: List[float]
    colors: List[int]
    units: Optional[str]


def decode_header(blob: bytes) -> SgeoHeader:
    """Parse the 16-byte header without touching the body.

    Lets a caller dispatch on primitive type (or skip a blob it cannot handle)
    before paying for a full decode.
    """
    if len(blob) < HEADER_SIZE:
        raise SgeoDecodeError(
            f"SGEO blob is {len(blob)} bytes, shorter than the "
            f"{HEADER_SIZE}-byte header."
        )
    if blob[0:4] != MAGIC:
        raise SgeoDecodeError(f"Bad SGEO magic {blob[0:4]!r}, expected {MAGIC!r}.")
    version = blob[4]
    if version != VERSION_1:
        raise SgeoDecodeError(
            f"Unsupported SGEO version {version}, expected {VERSION_1}."
        )
    flags_raw, units_code, _reserved, crc = struct.unpack_from("<HHHI", blob, 6)
    return SgeoHeader(
        version=version,
        primitive_type=blob[5],
        flags=Flags(flags_raw),
        units_code=units_code,
        crc=crc,
    )


def verify_crc(blob: bytes) -> None:
    """Raise when the stored CRC does not match the body bytes.

    Cheap (one zlib call), and the only integrity check the format carries — a
    truncated download otherwise surfaces as garbage coordinates rather than an
    error.
    """
    header = decode_header(blob)
    actual = crc32(blob[HEADER_SIZE:])
    if actual != header.crc:
        raise SgeoDecodeError(
            f"SGEO CRC mismatch: header says {header.crc:#010x}, "
            f"body hashes to {actual:#010x}."
        )


def decode_mesh(blob: bytes, *, verify: bool = True) -> DecodedMesh:
    """Decode a MESH blob into its raw arrays.

    Mirrors :func:`_encode_mesh` byte for byte, including its two asymmetric
    alignment rules: normals and UVs are each preceded by a pad to the next
    8-byte boundary, colours are **not**.

    Only ``vertex_count`` and ``face_count`` are stored, so the optional array
    lengths are derived from the vertex count (3 per vertex for normals, 2 for
    UVs, 1 for colours) — the format has no room for anything else.
    """
    header = decode_header(blob)
    if header.primitive_type != PrimitiveType.MESH:
        primitive = header.primitive
        name = primitive.name if primitive else f"code {header.primitive_type}"
        raise SgeoDecodeError(f"Expected a MESH blob, got {name}.")
    if verify:
        verify_crc(blob)

    body = memoryview(blob)[HEADER_SIZE:]
    vertex_count, face_count = struct.unpack_from("<II", body, 0)

    offset = 8
    vertices, offset = _read_f64_array(body, offset, vertex_count * 3, "vertices")
    faces, offset = _read_i32_array(body, offset, face_count, "faces")

    normals: List[float] = []
    if header.flags & Flags.HAS_NORMALS:
        offset = _align8(offset)
        normals, offset = _read_f64_array(body, offset, vertex_count * 3, "normals")

    uvs: List[float] = []
    if header.flags & Flags.HAS_UVS:
        offset = _align8(offset)
        uvs, offset = _read_f64_array(body, offset, vertex_count * 2, "UVs")

    colors: List[int] = []
    if header.flags & Flags.HAS_COLORS:
        # No pad before colours — mirrors the encoder's documented asymmetry.
        colors, offset = _read_i32_array(body, offset, vertex_count, "colors")

    return DecodedMesh(
        vertices=vertices,
        faces=faces,
        vertex_normals=normals,
        texture_coordinates=uvs,
        colors=colors,
        units=header.units,
    )


def decode(blob: bytes, *, verify: bool = True) -> Base:
    """Decode an SGEO v1 blob into the Speckle object it was encoded from.

    The inverse of :func:`encode`, covering every primitive the encoder emits.

    Raises:
        SgeoDecodeError: on a malformed blob or an unknown primitive code.
    """
    header = decode_header(blob)
    primitive = header.primitive
    if primitive is None:
        raise SgeoDecodeError(f"Unknown SGEO primitive code {header.primitive_type}.")
    if verify:
        verify_crc(blob)

    if primitive is PrimitiveType.MESH:
        # the raw path already builds the arrays; just wrap them
        from specklepy.objects.geometry.mesh import Mesh

        mesh = decode_mesh(blob, verify=False)
        return Mesh(
            vertices=mesh.vertices,
            faces=mesh.faces,
            vertexNormals=mesh.vertex_normals,
            textureCoordinates=mesh.texture_coordinates,
            colors=mesh.colors,
            units=mesh.units,
        )

    decoder = _DECODERS.get(primitive)
    if decoder is None:
        raise SgeoDecodeError(f"No SGEO decoder for primitive {primitive.name}.")
    return decoder(header, _Reader(memoryview(blob)[HEADER_SIZE:]))


# ── per-primitive decoders ─────────────────────────────────────────────────
#
# Each inverts the matching ``_encode_*`` above; read them side by side. The
# encoders are the specification — where a field is *derived* rather than stored
# (a Circle's centre, an array length) it is called out, because that is where a
# decoder silently invents data if it guesses wrong.


def _decode_line(header: SgeoHeader, r: _Reader) -> Base:
    from specklepy.objects.geometry.line import Line

    domain = r.interval()
    start = r.point(header.units)
    end = r.point(header.units)
    line = Line(start=start, end=end, units=header.units)
    line.domain = domain
    return line


def _decode_polyline(header: SgeoHeader, r: _Reader) -> Base:
    from specklepy.objects.geometry.polyline import Polyline

    count = r.u32()
    r.u32()  # reserved
    polyline = Polyline(value=r.f64s(count * 3), units=header.units)
    # Polyline has no `closed` field — it computes is_closed() from its points —
    # so the flag round-trips as the dynamic member the producer set.
    polyline["closed"] = bool(header.flags & Flags.CLOSED)
    return polyline


def _decode_polycurve(header: SgeoHeader, r: _Reader) -> Base:
    from specklepy.objects.geometry.polycurve import Polycurve

    count = r.u32()
    r.u32()  # reserved
    segments = []
    for _ in range(count):
        length = r.u32()
        r.u32()  # reserved
        # each segment is a complete nested SGEO blob whose bytes (CRC field
        # included) the outer body CRC already covers, so never re-verify —
        # the same handoff decode() makes for MESH via decode_mesh
        segments.append(decode(r.blob(length), verify=False))
        r.align8()
    return Polycurve(segments=segments, units=header.units)


def _decode_curve(header: SgeoHeader, r: _Reader) -> Base:
    from specklepy.objects.geometry.curve import Curve

    display = r.polyline_body(header.units, closed=bool(header.flags & Flags.CLOSED))

    degree = r.u32()
    point_count = r.u32()
    knot_count = r.u32()
    r.u32()  # reserved
    domain = r.interval()

    points = r.f64s(point_count * 3)
    rational = bool(header.flags & Flags.RATIONAL)
    # weights are written only when rational, one per control point — the count
    # is not stored, so it has to come from point_count
    weights = r.f64s(point_count) if rational else []
    knots = r.f64s(knot_count)

    curve = Curve(
        degree=degree,
        periodic=bool(header.flags & Flags.PERIODIC),
        rational=rational,
        points=points,
        weights=weights,
        knots=knots,
        # NB: the encoder sets CLOSED from `_is_closed(c.displayValue)`, not from
        # `c.closed` — the field itself never reaches the wire. For a producer
        # that keeps the two in step (Blender sets both from `use_cyclic_u`) this
        # is faithful; for one that disagrees, the display polyline wins.
        closed=bool(header.flags & Flags.CLOSED),
        displayValue=display,
        units=header.units,
        bbox=None,
    )
    curve.domain = domain
    return curve


def _decode_arc(header: SgeoHeader, r: _Reader) -> Base:
    from specklepy.objects.geometry.arc import Arc

    plane = r.plane(header.units)
    start = r.point(header.units)
    mid = r.point(header.units)
    end = r.point(header.units)
    arc = Arc(
        plane=plane,
        startPoint=start,
        midPoint=mid,
        endPoint=end,
        units=header.units,
    )
    arc.domain = r.interval()
    return arc


def _decode_circle(header: SgeoHeader, r: _Reader) -> Base:
    from specklepy.objects.geometry.circle import Circle

    radius = r.f64()
    domain = r.interval()
    plane = r.plane(header.units)
    # `center` is not on the wire: the encoder writes only radius + domain +
    # plane, and a circle's centre is its plane origin by construction.
    circle = Circle(plane=plane, center=plane.origin, radius=radius, units=header.units)
    circle.domain = domain
    return circle


def _decode_points(header: SgeoHeader, r: _Reader) -> Base:
    from specklepy.objects.geometry.point import Point
    from specklepy.objects.geometry.point_cloud import PointCloud

    count = r.u32()
    r.u32()  # reserved
    coords = r.f64s(count * 3)

    colors = r.i32s(count) if header.flags & Flags.HAS_COLORS else []
    sizes: List[float] = []
    if header.flags & Flags.HAS_SIZES:
        r.align8()
        sizes = r.f64s(count)

    # A lone Point and a one-point PointCloud with no colours or sizes encode to
    # identical bytes, so the distinction cannot be recovered. Prefer Point: it
    # is what a single-point blob almost always was, and it is the cheaper shape.
    if count == 1 and not colors and not sizes:
        return Point(x=coords[0], y=coords[1], z=coords[2], units=header.units)

    points = [
        Point(
            x=coords[i],
            y=coords[i + 1],
            z=coords[i + 2],
            units=header.units,
        )
        for i in range(0, len(coords), 3)
    ]
    cloud = PointCloud(points=points, units=header.units)
    if colors:
        cloud["colors"] = colors
    if sizes:
        cloud["sizes"] = sizes
    return cloud


def _decode_ellipse(header: SgeoHeader, r: _Reader) -> Base:
    from specklepy.objects.geometry.ellipse import Ellipse

    first_radius = r.f64()
    second_radius = r.f64()
    domain = r.interval()
    plane = r.plane(header.units)

    ellipse = Ellipse(
        plane=plane,
        first_radius=first_radius,
        second_radius=second_radius,
        units=header.units,
    )
    ellipse.domain = domain
    if header.flags & Flags.HAS_TRIM_DOMAIN:
        ellipse["trimDomain"] = r.interval()
    return ellipse


def _decode_spiral(header: SgeoHeader, r: _Reader) -> Base:
    from specklepy.objects.geometry.spiral import Spiral

    display = r.polyline_body(header.units, closed=bool(header.flags & Flags.CLOSED))

    spiral_type = r.u32()
    r.u32()  # reserved
    start = r.point(header.units)
    end = r.point(header.units)
    plane = r.plane(header.units)
    turns = r.f64()
    pitch_axis = r.vector(header.units)
    pitch = r.f64()
    domain = r.interval()

    spiral = Spiral(
        start_point=start,
        end_point=end,
        plane=plane,
        turns=turns,
        pitch=pitch,
        pitch_axis=pitch_axis,
        units=header.units,
    )
    spiral.domain = domain
    spiral["spiralType"] = spiral_type
    # an all-zero leading polyline means the producer had no displayValue
    if display.value:
        spiral["displayValue"] = display
    return spiral


def _decode_box(header: SgeoHeader, r: _Reader) -> Base:
    from specklepy.objects.geometry.box import Box

    plane = r.plane(header.units)
    return Box(
        basePlane=plane,
        xSize=r.interval(),
        ySize=r.interval(),
        zSize=r.interval(),
        units=header.units,
    )


_DECODERS = {
    PrimitiveType.LINE: _decode_line,
    PrimitiveType.POLYLINE: _decode_polyline,
    PrimitiveType.POLYCURVE: _decode_polycurve,
    PrimitiveType.CURVE: _decode_curve,
    PrimitiveType.ARC: _decode_arc,
    PrimitiveType.CIRCLE: _decode_circle,
    PrimitiveType.POINTS: _decode_points,
    PrimitiveType.ELLIPSE: _decode_ellipse,
    PrimitiveType.SPIRAL: _decode_spiral,
    PrimitiveType.BOX: _decode_box,
}


# ── low-level body readers ─────────────────────────────────────────────────


class _Reader:
    """A cursor over an SGEO body, mirroring the encoder's writers one for one.

    Offsets are body-relative, which is what makes :meth:`align8` the exact
    inverse of :func:`_pad8` — the body always starts 8-aligned at 0x10, so the
    two agree.
    """

    __slots__ = ("_body", "offset")

    def __init__(self, body: memoryview) -> None:
        self._body = body
        self.offset = 0

    def _take(self, size: int, label: str) -> int:
        start = self.offset
        if start + size > len(self._body):
            raise SgeoDecodeError(
                f"SGEO body truncated reading {label}: need {size} bytes at "
                f"offset {start}, only {max(0, len(self._body) - start)} remain."
            )
        self.offset = start + size
        return start

    def u32(self) -> int:
        return struct.unpack_from("<I", self._body, self._take(4, "uint32"))[0]

    def f64(self) -> float:
        return struct.unpack_from("<d", self._body, self._take(8, "float64"))[0]

    def f64s(self, count: int) -> List[float]:
        if count <= 0:
            return []
        at = self._take(count * 8, f"{count} float64s")
        return list(struct.unpack_from(f"<{count}d", self._body, at))

    def i32s(self, count: int) -> List[int]:
        if count <= 0:
            return []
        at = self._take(count * 4, f"{count} int32s")
        return list(struct.unpack_from(f"<{count}i", self._body, at))

    def blob(self, size: int) -> bytes:
        at = self._take(size, f"{size}-byte nested blob")
        return bytes(self._body[at : at + size])

    def align8(self) -> None:
        self.offset = _align8(self.offset)

    def interval(self):
        from specklepy.objects.primitive import Interval

        return Interval(start=self.f64(), end=self.f64())

    def point(self, units: Optional[str]):
        from specklepy.objects.geometry.point import Point

        return Point(x=self.f64(), y=self.f64(), z=self.f64(), units=units)

    def vector(self, units: Optional[str]):
        from specklepy.objects.geometry.vector import Vector

        return Vector(x=self.f64(), y=self.f64(), z=self.f64(), units=units)

    def plane(self, units: Optional[str]):
        from specklepy.objects.geometry.plane import Plane

        return Plane(
            origin=self.point(units),
            normal=self.vector(units),
            xdir=self.vector(units),
            ydir=self.vector(units),
            units=units,
        )

    def polyline_body(self, units: Optional[str], closed: bool = False):
        """Read the render polyline that leads a CURVE or SPIRAL body.

        The inverse of :func:`_polyline_body`, trailing ``_pad8`` included — the
        analytical definition that follows is f64-aligned only because of it.
        """
        from specklepy.objects.geometry.polyline import Polyline

        count = self.u32()
        self.u32()  # reserved
        value = self.f64s(count * 3)
        self.align8()
        polyline = Polyline(value=value, units=units)
        polyline["closed"] = closed
        return polyline


def _align8(offset: int) -> int:
    """Skip to the next 8-byte boundary — the read side of :func:`_pad8`."""
    return offset + (-offset % 8)


def _ensure_available(body: memoryview, offset: int, size: int, label: str) -> None:
    if offset + size > len(body):
        raise SgeoDecodeError(
            f"SGEO body truncated reading {label}: need {size} bytes at offset "
            f"{offset}, only {max(0, len(body) - offset)} remain."
        )


def _read_f64_array(
    body: memoryview, offset: int, count: int, label: str
) -> Tuple[List[float], int]:
    if count == 0:
        return [], offset
    size = count * 8
    _ensure_available(body, offset, size, label)
    values = list(struct.unpack_from(f"<{count}d", body, offset))
    return values, offset + size


def _read_i32_array(
    body: memoryview, offset: int, count: int, label: str
) -> Tuple[List[int], int]:
    """Read ``count`` signed 32-bit words.

    Signed on the way out even though the encoder packs unsigned: ``Mesh.colors``
    holds signed ARGB ints, and face indices never exceed int32 anyway, so
    signed is the layout that round-trips.
    """
    if count == 0:
        return [], offset
    size = count * 4
    _ensure_available(body, offset, size, label)
    values = list(struct.unpack_from(f"<{count}i", body, offset))
    return values, offset + size
