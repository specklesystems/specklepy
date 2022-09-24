from enum import Enum
from typing import Any, List, Optional

from .base import Base
from .encoding import CurveArray, CurveTypeEncoding, ObjectArray
from .units import get_encoding_from_units, get_units_from_encoding

GEOMETRY = "Objects.Geometry."


class Interval(Base, speckle_type="Objects.Primitive.Interval"):
    start: float = 0.0
    end: float = 0.0

    def length(self):
        return abs(self.start - self.end)

    @classmethod
    def from_list(cls, args: List[Any]) -> "Interval":
        return cls(start=args[0], end=args[1])

    def to_list(self) -> List[Any]:
        return [self.start, self.end]


class Point(Base, speckle_type=GEOMETRY + "Point"):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x: {self.x}, y: {self.y}, z: {self.z}, id: {self.id}, speckle_type: {self.speckle_type})"

    @classmethod
    def from_list(cls, args: List[float]) -> "Point":
        """Create a new Point from a list of three floats representing the x, y, and z coordinates"""
        return cls(x=args[0], y=args[1], z=args[2])

    def to_list(self) -> List[Any]:
        return [self.x, self.y, self.z]

    @classmethod
    def from_coords(cls, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        """Create a new Point from x, y, and z values"""
        pt = Point()
        pt.x, pt.y, pt.z = x, y, z
        return pt


class Vector(Point, speckle_type=GEOMETRY + "Vector"):
    pass


class ControlPoint(Point, speckle_type=GEOMETRY + "ControlPoint"):
    weight: float = None


class Plane(Base, speckle_type=GEOMETRY + "Plane"):
    origin: Point = Point()
    normal: Vector = Vector()
    xdir: Vector = Vector()
    ydir: Vector = Vector()

    @classmethod
    def from_list(cls, args: List[Any]) -> "Plane":
        return cls(
            origin=Point.from_list(args[:3]),
            normal=Vector.from_list(args[3:6]),
            xdir=Vector.from_list(args[6:9]),
            ydir=Vector.from_list(args[9:12]),
            units=get_units_from_encoding(args[-1]),
        )

    def to_list(self) -> List[Any]:
        return [
            *self.origin.to_list(),
            *self.normal.to_list(),
            *self.xdir.to_list(),
            *self.ydir.to_list(),
            get_encoding_from_units(self._units),
        ]


class Box(Base, speckle_type=GEOMETRY + "Box"):
    basePlane: Plane = Plane()
    ySize: Interval = Interval()
    zSize: Interval = Interval()
    xSize: Interval = Interval()
    area: float = None
    volume: float = None


class Line(Base, speckle_type=GEOMETRY + "Line"):
    start: Point = Point()
    end: Point = None
    domain: Interval = None
    bbox: Box = None
    length: float = None

    @classmethod
    def from_list(cls, args: List[Any]) -> "Line":
        return cls(
            start=Point.from_list(args[1:4]),
            end=Point.from_list(args[4:7]),
            domain=Interval.from_list(args[7:10]),
            units=get_units_from_encoding(args[-1]),
        )

    def to_list(self) -> List[Any]:
        domain = self.domain.to_list() if self.domain else [0, 1]
        return [
            CurveTypeEncoding.Line.value,
            *self.start.to_list(),
            *self.end.to_list(),
            *domain,
            get_encoding_from_units(self._units),
        ]


class Arc(Base, speckle_type=GEOMETRY + "Arc"):
    radius: float = None
    startAngle: float = None
    endAngle: float = None
    angleRadians: float = None
    plane: Plane = None
    domain: Interval = None
    startPoint: Point = None
    midPoint: Point = None
    endPoint: Point = None
    bbox: Box = None
    area: float = None
    length: float = None

    @classmethod
    def from_list(cls, args: List[Any]) -> "Arc":
        return cls(
            radius=args[1],
            startAngle=args[2],
            endAngle=args[3],
            angleRadians=args[4],
            domain=Interval.from_list(args[5:7]),
            plane=Plane.from_list(args[7:20]),
            startPoint=Point.from_list(args[20:23]),
            midPoint=Point.from_list(args[23:26]),
            endPoint=Point.from_list(args[26:29]),
            units=get_units_from_encoding(args[-1]),
        )

    def to_list(self) -> List[Any]:
        return [
            CurveTypeEncoding.Arc.value,
            self.radius,
            self.startAngle,
            self.endAngle,
            self.angleRadians,
            *self.domain.to_list(),
            *self.plane.to_list(),
            *self.startPoint.to_list(),
            *self.midPoint.to_list(),
            *self.endPoint.to_list(),
            get_encoding_from_units(self._units),
        ]


class Circle(Base, speckle_type=GEOMETRY + "Circle"):
    radius: float = None
    plane: Plane = None
    domain: Interval = None
    bbox: Box = None
    area: float = None
    length: float = None

    @classmethod
    def from_list(cls, args: List[Any]) -> "Circle":
        return cls(
            radius=args[1],
            domain=Interval.from_list(args[2:4]),
            plane=Plane.from_list(args[4:17]),
            units=get_units_from_encoding(args[-1]),
        )

    def to_list(self) -> List[Any]:
        return [
            CurveTypeEncoding.Circle.value,
            self.radius,
            *self.domain.to_list(),
            *self.plane.to_list(),
            get_encoding_from_units(self._units),
        ]


class Ellipse(Base, speckle_type=GEOMETRY + "Ellipse"):
    firstRadius: float = None
    secondRadius: float = None
    plane: Plane = None
    domain: Interval = None
    trimDomain: Interval = None
    bbox: Box = None
    area: float = None
    length: float = None

    @classmethod
    def from_list(cls, args: List[Any]) -> "Ellipse":
        return cls(
            firstRadius=args[1],
            secondRadius=args[2],
            domain=Interval.from_list(args[3:5]),
            plane=Plane.from_list(args[5:18]),
            units=get_units_from_encoding(args[-1]),
        )

    def to_list(self) -> List[Any]:
        return [
            CurveTypeEncoding.Ellipse.value,
            self.firstRadius,
            self.secondRadius,
            *self.domain.to_list(),
            *self.plane.to_list(),
            get_encoding_from_units(self._units),
        ]


class Polyline(Base, speckle_type=GEOMETRY + "Polyline", chunkable={"value": 20000}):
    value: List[float] = None
    closed: bool = None
    domain: Interval = None
    bbox: Box = None
    area: float = None
    length: float = None

    @classmethod
    def from_points(cls, points: List[Point]):
        """Create a new Polyline from a list of Points"""
        polyline = cls()
        polyline.units = points[0].units
        polyline.value = []
        for point in points:
            polyline.value.extend([point.x, point.y, point.z])
        return polyline

    @classmethod
    def from_list(cls, args: List[Any]) -> "Polyline":
        point_count = args[4]
        return cls(
            closed=bool(args[1]),
            domain=Interval.from_list(args[2:4]),
            value=args[5 : 5 + point_count],
            units=get_units_from_encoding(args[-1]),
        )

    def to_list(self) -> List[Any]:
        return [
            CurveTypeEncoding.Polyline.value,
            int(self.closed),
            *self.domain.to_list(),
            len(self.value),
            *self.value,
            get_encoding_from_units(self._units),
        ]

    def as_points(self) -> List[Point]:
        """Converts the `value` attribute to a list of Points"""
        if not self.value:
            return

        if len(self.value) % 3:
            raise ValueError("Points array malformed: length%3 != 0.")

        values = iter(self.value)
        return [
            Point(x=v, y=next(values), z=next(values), units=self.units) for v in values
        ]


class Curve(
    Base,
    speckle_type=GEOMETRY + "Curve",
    chunkable={"points": 20000, "weights": 20000, "knots": 20000},
):
    degree: int = None
    periodic: bool = None
    rational: bool = None
    points: List[float] = None
    weights: List[float] = None
    knots: List[float] = None
    domain: Interval = None
    displayValue: Polyline = None
    closed: bool = None
    bbox: Box = None
    area: float = None
    length: float = None

    def as_points(self) -> List[Point]:
        """Converts the `value` attribute to a list of Points"""
        if not self.points:
            return

        if len(self.points) % 3:
            raise ValueError("Points array malformed: length%3 != 0.")

        values = iter(self.points)
        return [
            Point(x=v, y=next(values), z=next(values), units=self.units) for v in values
        ]

    @classmethod
    def from_list(cls, args: List[Any]) -> "Curve":
        point_count = int(args[7])
        weights_count = int(args[8])
        knots_count = int(args[9])

        points_start = 10
        weights_start = 10 + point_count
        knots_start = weights_start + weights_count
        knots_end = knots_start + knots_count

        return cls(
            degree=int(args[1]),
            periodic=bool(args[2]),
            rational=bool(args[3]),
            closed=bool(args[4]),
            domain=Interval.from_list(args[5:7]),
            points=args[points_start:weights_start],
            weights=args[weights_start:knots_start],
            knots=args[knots_start:knots_end],
            units=get_units_from_encoding(args[-1]),
        )

    def to_list(self) -> List[Any]:
        return [
            CurveTypeEncoding.Curve.value,
            self.degree,
            int(self.periodic),
            int(self.rational),
            int(self.closed),
            *self.domain.to_list(),
            len(self.points),
            len(self.weights),
            len(self.knots),
            *self.points,
            *self.weights,
            *self.knots,
            get_encoding_from_units(self._units),
        ]


class Polycurve(Base, speckle_type=GEOMETRY + "Polycurve"):
    segments: List[Base] = None
    domain: Interval = None
    closed: bool = None
    bbox: Box = None
    area: float = None
    length: float = None

    @classmethod
    def from_list(cls, args: List[Any]) -> "Polycurve":
        curve_arrays = CurveArray(args[5:-1])
        return cls(
            closed=bool(args[1]),
            domain=Interval.from_list(args[2:4]),
            segments=curve_arrays.to_curves(),
            units=get_units_from_encoding(args[-1]),
        )

    def to_list(self) -> List[Any]:
        curve_array = CurveArray.from_curves(self.segments).data
        return [
            CurveTypeEncoding.Polycurve.value,
            int(self.closed),
            *self.domain.to_list(),
            len(curve_array),
            *curve_array,
            get_encoding_from_units(self._units),
        ]


class Extrusion(Base, speckle_type=GEOMETRY + "Extrusion"):
    capped: bool = None
    profile: Base = None
    pathStart: Point = None
    pathEnd: Point = None
    pathCurve: Base = None
    pathTangent: Base = None
    profiles: List[Base] = None
    length: float = None
    area: float = None
    volume: float = None
    bbox: Box = None


class Mesh(
    Base,
    speckle_type=GEOMETRY + "Mesh",
    chunkable={
        "vertices": 2000,
        "faces": 2000,
        "colors": 2000,
        "textureCoordinates": 2000,
    },
):
    vertices: List[float] = None
    faces: List[int] = None
    colors: List[int] = None
    textureCoordinates: List[float] = None
    bbox: Box = None
    area: float = None
    volume: float = None

    @classmethod
    def create(
        cls,
        vertices: List[float],
        faces: List[int],
        colors: List[int] = None,
        texture_coordinates: List[float] = None,
    ) -> "Mesh":
        """
        Create a new Mesh from lists representing its vertices, faces,
        colors (optional), and texture coordinates (optional).

        This will initialise empty lists for colors and texture coordinates
        if you do not provide any.
        """
        return cls(
            vertices=vertices,
            faces=faces,
            colors=colors or [],
            textureCoordinates=texture_coordinates or [],
        )


class Surface(Base, speckle_type=GEOMETRY + "Surface"):
    degreeU: int = None
    degreeV: int = None
    rational: bool = None
    area: float = None
    pointData: List[float] = None
    countU: int = None
    countV: int = None
    bbox: Box = None
    closedU: bool = None
    closedV: bool = None
    domainU: Interval = None
    domainV: Interval = None
    knotsU: List[float] = None
    knotsV: List[float] = None

    @classmethod
    def from_list(cls, args: List[Any]) -> "Surface":
        point_count = int(args[11])
        knots_u_count = int(args[12])
        knots_v_count = int(args[13])

        start_point_data = 14
        start_knots_u = start_point_data + point_count
        start_knots_v = start_knots_u + knots_u_count

        return cls(
            degreeU=int(args[0]),
            degreeV=int(args[1]),
            countU=int(args[2]),
            countV=int(args[3]),
            rational=bool(args[4]),
            closedU=bool(args[5]),
            closedV=bool(args[6]),
            domainU=Interval(start=args[7], end=args[8]),
            domainV=Interval(start=args[9], end=args[10]),
            pointData=args[start_point_data:start_knots_u],
            knotsU=args[start_knots_u:start_knots_v],
            knotsV=args[start_knots_v : start_knots_v + knots_v_count],
            units=get_units_from_encoding(args[-1]),
        )

    def to_list(self) -> List[Any]:
        return [
            self.degreeU,
            self.degreeV,
            self.countU,
            self.countV,
            int(self.rational),
            int(self.closedU),
            int(self.closedV),
            *self.domainU.to_list(),
            *self.domainV.to_list(),
            len(self.pointData),
            len(self.knotsU),
            len(self.knotsV),
            *self.pointData,
            *self.knotsU,
            *self.knotsV,
            get_encoding_from_units(self._units),
        ]


class BrepFace(Base, speckle_type=GEOMETRY + "BrepFace"):
    _Brep: "Brep" = None
    SurfaceIndex: int = None
    OuterLoopIndex: int = None
    OrientationReversed: bool = None
    LoopIndices: List[int] = None

    @property
    def _outer_loop(self):
        return self._Brep.Loops[self.OuterLoopIndex]  # pylint: disable=no-member

    @property
    def _surface(self):
        return self._Brep.Surfaces[self.SurfaceIndex]  # pylint: disable=no-member

    @property
    def _loops(self):
        if self.LoopIndices:
            # pylint: disable=not-an-iterable, no-member
            return [self._Brep.Loops[i] for i in self.LoopIndices]

    @classmethod
    def from_list(cls, args: List[Any], brep: "Brep" = None) -> "BrepFace":
        return cls(
            _Brep=brep,
            SurfaceIndex=args[0],
            OuterLoopIndex=args[1],
            OrientationReversed=bool(args[2]),
            LoopIndices=args[3:],
        )

    def to_list(self) -> List[Any]:
        return [
            self.SurfaceIndex,
            self.OuterLoopIndex,
            int(self.OrientationReversed),
            *self.LoopIndices,
        ]


class BrepEdge(Base, speckle_type=GEOMETRY + "BrepEdge"):
    _Brep: "Brep" = None
    Curve3dIndex: int = None
    TrimIndices: List[int] = None
    StartIndex: int = None
    EndIndex: int = None
    ProxyCurveIsReversed: bool = None
    Domain: Interval = None

    @property
    def _start_vertex(self):
        return self._Brep.Vertices[self.StartIndex]

    @property
    def _end_vertex(self):
        return self._Brep.Vertices[self.EndIndex]

    @property
    def _trims(self):
        if self.TrimIndices:
            # pylint: disable=not-an-iterable
            return [self._Brep.Trims[i] for i in self.TrimIndices]

    @property
    def _curve(self):
        return self._Brep.Curve3D[self.Curve3dIndex]

    @classmethod
    def from_list(cls, args: List[Any], brep: "Brep" = None) -> "BrepEdge":
        domain_start = args[4]
        domain_end = args[5]
        domain = (
            Interval(start=domain_start, end=domain_end)
            if None not in (domain_start, domain_end)
            else None
        )
        return cls(
            _Brep=brep,
            Curve3dIndex=int(args[0]),
            TrimIndices=[int(t) for t in args[6:]],
            StartIndex=int(args[1]),
            EndIndex=int(args[2]),
            ProxyCurveIsReversed=bool(args[3]),
            Domain=domain,
        )

    def to_list(self) -> List[Any]:
        return [
            self.Curve3dIndex,
            self.StartIndex,
            self.EndIndex,
            int(self.ProxyCurveIsReversed),
            self.Domain.start,
            self.Domain.end,
            *self.TrimIndices,
        ]


class BrepLoopType(int, Enum):
    Unknown = 0
    Outer = 1
    Inner = 2
    Slit = 3
    CurveOnSurface = 4
    PointOnSurface = 5


class BrepLoop(Base, speckle_type=GEOMETRY + "BrepLoop"):
    _Brep: "Brep" = None
    FaceIndex: int = None
    TrimIndices: List[int] = None
    Type: BrepLoopType = None

    @property
    def _face(self):
        return self._Brep.Faces[self.FaceIndex]

    @property
    def _trims(self):
        if self.TrimIndices:
            # pylint: disable=not-an-iterable
            return [self._Brep.Trims[i] for i in self.TrimIndices]

    @classmethod
    def from_list(cls, args: List[any], brep: "Brep" = None):
        return cls(
            _Brep=brep,
            FaceIndex=args[0],
            Type=BrepLoopType(args[1]),
            TrimIndices=args[2:],
        )

    def to_list(self) -> List[int]:
        return [
            self.FaceIndex,
            self.Type.value,
            *self.TrimIndices,
        ]


class BrepTrimType(int, Enum):
    Unknown = 0
    Boundary = 1
    Mated = 2
    Seam = 3
    Singular = 4
    CurveOnSurface = 5
    PointOnSurface = 6
    Slit = 7


class BrepTrim(Base, speckle_type=GEOMETRY + "BrepTrim"):
    _Brep: "Brep" = None
    EdgeIndex: int = None
    StartIndex: int = None
    EndIndex: int = None
    FaceIndex: int = None
    LoopIndex: int = None
    CurveIndex: int = None
    IsoStatus: int = None
    TrimType: BrepTrimType = None
    IsReversed: bool = None
    Domain: Interval = None

    @property
    def _face(self):
        if self._Brep:
            return self._Brep.Faces[self.FaceIndex]  # pylint: disable=no-member

    @property
    def _loop(self):
        if self._Brep:
            return self._Brep.Loops[self.LoopIndex]  # pylint: disable=no-member

    @property
    def _edge(self):
        if self._Brep:
            # pylint: disable=no-member
            return self._Brep.Edges[self.EdgeIndex] if self.EdgeIndex != -1 else None

    @property
    def _curve_2d(self):
        if self._Brep:
            return self._Brep.Curve2D[self.CurveIndex]  # pylint: disable=no-member

    @classmethod
    def from_list(cls, args: List[Any], brep: "Brep" = None) -> "BrepTrim":
        return cls(
            _Brep=brep,
            EdgeIndex=args[0],
            StartIndex=args[1],
            EndIndex=args[2],
            FaceIndex=args[3],
            LoopIndex=args[4],
            CurveIndex=args[5],
            IsoStatus=args[6],
            TrimType=BrepTrimType(args[7]),
            IsReversed=bool(args[8]),
        )

    def to_list(self) -> List[Any]:
        return [
            self.EdgeIndex,
            self.StartIndex,
            self.EndIndex,
            self.FaceIndex,
            self.LoopIndex,
            self.CurveIndex,
            self.IsoStatus,
            self.TrimType.value,
            int(self.IsReversed),
        ]


class Brep(
    Base,
    speckle_type=GEOMETRY + "Brep",
    chunkable={
        "SurfacesValue": 31250,
        "Curve3DValues": 31250,
        "Curve2DValues": 31250,
        "VerticesValue": 31250,
        "EdgesValue": 62500,
        "LoopsValue": 62500,
        "FacesValue": 62500,
        "TrimsValue": 62500,
    },
    detachable={"displayValue"},
    serialize_ignore={
        "Surfaces",
        "Curve3D",
        "Curve2D",
        "Vertices",
        "Trims",
        "Edges",
        "Loops",
        "Faces",
    },
):
    provenance: str = None
    bbox: Box = None
    area: float = None
    volume: float = None
    _displayValue: List[Mesh] = None
    Surfaces: List[Surface] = None
    Curve3D: List[Base] = None
    Curve2D: List[Base] = None
    Vertices: List[Point] = None
    Edges: List[BrepEdge] = None
    Loops: List[BrepLoop] = None
    Faces: List[BrepFace] = None
    Trims: List[BrepTrim] = None
    IsClosed: bool = None
    Orientation: int = None

    def _inject_self_into_children(self, children: Optional[List[Base]]) -> List[Base]:
        if children is None:
            return children

        for child in children:
            child._Brep = self  # pylint: disable=protected-access
        return children

    # set as prop for now for backwards compatibility
    @property
    def displayValue(self) -> List[Mesh]:
        return self._displayValue

    @displayValue.setter
    def displayValue(self, value):
        if isinstance(value, Mesh):
            self._displayValue = [value]
        elif isinstance(value, list):
            self._displayValue = value

    @property
    def EdgesValue(self) -> List[BrepEdge]:
        return None if self.Edges is None else ObjectArray.from_objects(self.Edges).data

    @EdgesValue.setter
    def EdgesValue(self, value: List[float]):
        if not value:
            return

        self.Edges = ObjectArray.decode_data(value, BrepEdge.from_list, brep=self)

    @property
    def LoopsValue(self) -> List[BrepLoop]:
        return None if self.Loops is None else ObjectArray.from_objects(self.Loops).data

    @LoopsValue.setter
    def LoopsValue(self, value: List[int]):
        if not value:
            return

        self.Loops = ObjectArray.decode_data(value, BrepLoop.from_list, brep=self)

    @property
    def FacesValue(self) -> List[int]:
        return None if self.Faces is None else ObjectArray.from_objects(self.Faces).data

    @FacesValue.setter
    def FacesValue(self, value: List[int]):
        if not value:
            return

        self.Faces = ObjectArray.decode_data(value, BrepFace.from_list, brep=self)

    @property
    def SurfacesValue(self) -> List[float]:
        return (
            None
            if self.Surfaces is None
            else ObjectArray.from_objects(self.Surfaces).data
        )

    @SurfacesValue.setter
    def SurfacesValue(self, value: List[float]):
        if not value:
            return

        self.Surfaces = ObjectArray.decode_data(value, Surface.from_list)

    @property
    def Curve3DValues(self) -> List[float]:
        return (
            None if self.Curve3D is None else CurveArray.from_curves(self.Curve3D).data
        )

    @Curve3DValues.setter
    def Curve3DValues(self, value: List[float]):
        crv_array = CurveArray(value)
        self.Curve3D = crv_array.to_curves()

    @property
    def Curve2DValues(self) -> List[Base]:
        return (
            None if self.Curve2D is None else CurveArray.from_curves(self.Curve2D).data
        )

    @Curve2DValues.setter
    def Curve2DValues(self, value: List[float]):
        crv_array = CurveArray(value)
        self.Curve2D = crv_array.to_curves()

    @property
    def VerticesValue(self) -> List[Point]:
        if self.Vertices is None:
            return None
        encoded_unit = get_encoding_from_units(self.Vertices[0]._units)
        values = [encoded_unit]
        for vertex in self.Vertices:
            values.extend(vertex.to_list())
        return values

    @VerticesValue.setter
    def VerticesValue(self, value: List[float]):
        value = value.copy()
        units = get_units_from_encoding(value.pop(0))

        vertices = []

        for i in range(0, len(value), 3):
            vertex = Point.from_list(value[i : i + 3])
            vertex._units = units
            vertices.append(vertex)

        self.Vertices = vertices

    # TODO: can this be consistent with loops, edges, faces, curves, etc and prepend with the chunk list? needs to happen in sharp first
    @property
    def TrimsValue(self) -> List[float]:
        # return None if self.Trims is None else ObjectArray.from_objects(self.Trims).data
        if not self.Trims:
            return
        value = []
        for trim in self.Trims:
            value.extend(trim.to_list())
        return value

    @TrimsValue.setter
    def TrimsValue(self, value: List[float]):
        if not value:
            return

        # self.Trims = ObjectArray.decode_data(value, BrepTrim.from_list, brep=self)
        self.Trims = [
            BrepTrim.from_list(value[i : i + 9], self) for i in range(0, len(value), 9)
        ]


BrepEdge.update_forward_refs()
BrepLoop.update_forward_refs()
BrepTrim.update_forward_refs()
BrepFace.update_forward_refs()
