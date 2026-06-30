"""SGEO v1 geometry encoder — a byte-for-byte port of the .NET ``SgeoEncoder``.

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
"""

from __future__ import annotations

import struct
from enum import IntEnum, IntFlag
from typing import Optional

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


def _build_crc_table() -> list[int]:
    table = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (0xEDB88820 ^ (c >> 1)) if (c & 1) else (c >> 1)
        table.append(c)
    return table


_CRC_TABLE = _build_crc_table()


def crc32(data: bytes) -> int:
    """SGEO body CRC — a direct port of SgeoFormat.Crc32 (poly ``0xEDB88820``).

    WARNING: the .NET SDK's ``Crc32`` uses the constant ``0xEDB88820`` (see
    ``SgeoFormat.cs``), which is NOT the canonical IEEE-802.3 reflected
    polynomial ``0xEDB88320``. The two differ by one bit, so SGEO's CRC does
    NOT match :func:`zlib.crc32`. We deliberately replicate the .NET constant
    so the header bytes are byte-for-byte identical to the C# encoder; do not
    "optimise" this to ``zlib.crc32`` — that would corrupt cross-SDK decoding.
    """
    crc = 0xFFFFFFFF
    for b in data:
        crc = _CRC_TABLE[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return crc ^ 0xFFFFFFFF


# ── low-level body writers ─────────────────────────────────────────────────


def _f64(b: bytearray, v: float) -> None:
    b += struct.pack("<d", v)


def _i32(b: bytearray, v: int) -> None:
    # Low 32 bits, matching C# AddInt32's (byte)(v >> 8*i) over a 32-bit int.
    b += struct.pack("<I", v & 0xFFFFFFFF)


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
    for v in m.vertices:
        _f64(body, v)
    for f in m.faces:
        _i32(body, f)
    if has_normals:
        _pad8(body)
        for n in m.vertexNormals:
            _f64(body, n)
    if has_uvs:
        _pad8(body)
        for t in m.textureCoordinates:
            _f64(body, t)
    if has_colors:
        # NB: no pad before colors — matches the C# encoder exactly.
        for c in m.colors:
            _i32(body, c)

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
