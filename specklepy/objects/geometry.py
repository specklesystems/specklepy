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
            origin=Point.from_list(args[0:3]),
            normal=Vector.from_list(args[3:6]),
            xdir=Vector.from_list(args[6:9]),
            ydir=Vector.from_list(args[9:12]),
        )

    def to_list(self) -> List[Any]:
        encoded = []
        encoded.extend(self.origin.to_list())
        encoded.extend(self.normal.to_list())
        encoded.extend(self.xdir.to_list())
        encoded.extend(self.ydir.to_list())
        return encoded


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
            start=Point.from_list(args[0:3]),
            end=Point.from_list(args[3:6]),
            domain=Interval.from_list(args[6:9]),
        )

    def to_list(self) -> List[Any]:
        encoded = []
        encoded.extend(self.start.to_list())
        encoded.extend(self.end.to_list())
        encoded.extend(self.domain.to_list())
        return encoded


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
            units=get_units_from_encoding(args[-1]),
        )

    def to_list(self) -> List[Any]:
        encoded = []
        encoded.append(CurveTypeEncoding.Arc.value)
        encoded.append(self.radius)
        encoded.append(self.startAngle)
        encoded.append(self.endAngle)
        encoded.append(self.angleRadians)
        encoded.extend(self.domain.to_list())
        encoded.extend(self.plane.to_list())
        encoded.append(get_encoding_from_units(self.units))
        return encoded


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
        encoded = []
        encoded.append(CurveTypeEncoding.Circle.value)
        encoded.append(self.radius),
        encoded.extend(self.domain.to_list())
        encoded.extend(self.plane.to_list())
        encoded.append(get_encoding_from_units(self.units))
        return encoded


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
        encoded = []
        encoded.append(CurveTypeEncoding.Ellipse.value)
        encoded.append(self.firstRadius)
        encoded.append(self.secondRadius)
        encoded.extend(self.domain.to_list())
        encoded.extend(self.plane.to_list())
        encoded.append(get_encoding_from_units(self.units))
        return encoded


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
        encoded = []
        encoded.append(CurveTypeEncoding.Polyline.value)
        encoded.append(int(self.closed))
        encoded.extend(self.domain.to_list())
        encoded.append(len(self.value))
        encoded.extend(self.value)
        encoded.append(get_encoding_from_units(self.units))
        return encoded

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
        encoded = []
        encoded.append(CurveTypeEncoding.Curve.value)
        encoded.append(self.degree)
        encoded.append(int(self.periodic))
        encoded.append(int(self.rational))
        encoded.append(int(self.closed))
        encoded.extend(self.domain.to_list())
        encoded.append(len(self.points))
        encoded.append(len(self.weights))
        encoded.append(len(self.knots))
        encoded.extend(self.points)
        encoded.extend(self.weights)
        encoded.extend(self.knots)
        encoded.append(get_encoding_from_units(self.units))
        return encoded


class Polycurve(Base, speckle_type=GEOMETRY + "Polycurve"):
    segments: List[Base] = None
    domain: Interval = None
    closed: bool = None
    bbox: Box = None
    area: float = None
    length: float = None

    @classmethod
    def from_list(cls, args: List[Any]) -> "Polycurve":
        curve_arrays = CurveArray()
        curve_arrays.data = args[4:-1]
        return cls(
            closed=bool(args[1]),
            domain=Interval.from_list(args[2:4]),
            segments=curve_arrays.to_curves(),
            units=get_units_from_encoding(args[-1]),
        )

    def to_list(self) -> List[Any]:
        encoded = []
        encoded.append(CurveTypeEncoding.Polycurve.value)
        encoded.append(int(self.closed))
        encoded.extend(self.domain.to_list())
        curve_array = CurveArray.from_curves(self.segments)
        encoded.extend(curve_array.data)
        encoded.append(get_encoding_from_units(self.units))
        return encoded


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
        encoded = []
        encoded.append(self.degreeU)
        encoded.append(self.degreeV)
        encoded.append(self.countU)
        encoded.append(self.countV)
        encoded.append(int(self.rational))
        encoded.append(int(self.closedU))
        encoded.append(int(self.closedV))
        encoded.extend(self.domainU.to_list())
        encoded.extend(self.domainV.to_list())
        encoded.append(len(self.pointData))
        encoded.append(len(self.knotsU))
        encoded.append(len(self.knotsV))
        encoded.extend(self.pointData)
        encoded.extend(self.knotsU)
        encoded.extend(self.knotsV)
        encoded.append(get_encoding_from_units(self.units))
        return encoded


class BrepFace(Base, speckle_type=GEOMETRY + "BrepFace"):
    _Brep: "Brep" = None
    SurfaceIndex: int = None
    OuterLoopIndex: int = None
    OrientationReversed: bool = None
    LoopIndices: List[int] = None

    @property
    def _outer_loop(self):
        return self._Brep.Loops[self.OuterLoopIndex] # pylint: disable=no-member

    @property
    def _surface(self):
        return self._Brep.Surfaces[self.SurfaceIndex] # pylint: disable=no-member

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
            OrientationReversed=args[2] == 1,
            LoopIndices=args[3:]
        )

    def to_list(self) -> List[Any]:
        encoded = [
            0,
            self.SurfaceIndex,
            self.OuterLoopIndex,
            int(self.OuterLoopIndex),
            *self.LoopIndices
            ]
        encoded[0] = len(encoded) - 1
        return encoded


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
        domain = Interval(start=domain_start, end=domain_end) if None not in (domain_start, domain_end) else None
        return cls(
            _Brep=brep,
            Curve3dIndex=int(args[0]),
            TrimIndices=[int(t) for t in args[6:]],
            StartIndex=int(args[1]),
            EndIndex=int(args[2]),
            ProxyCurveIsReversed=bool(args[3]),
            Domain=domain
        )

    def to_list(self) -> List[Any]:
        encoded = [0,
        self.Curve3dIndex,
        self.StartIndex,
        self.EndIndex,
        int(self.ProxyCurveIsReversed),
        self.Domain.start,
        self.Domain.end,
        *self.TrimIndices,
        ]
        encoded[0] = len(encoded) - 1
        return encoded

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
            TrimIndices=args[2:]
        )

    def to_list(self) -> List[int]:
        encoded = [
            self.FaceIndex,
            self.Type.value,
            *self.TrimIndices,
        ]
        encoded[0] = len(encoded) - 1
        return encoded

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
            return self._Brep.Faces[self.FaceIndex] # pylint: disable=no-member

    @property
    def _loop(self):
        if self._Brep:
            return self._Brep.Loops[self.LoopIndex] # pylint: disable=no-member

    @property
    def _edge(self):
        if self._Brep:
            # pylint: disable=no-member
            return self._Brep.Edges[self.EdgeIndex] if self.EdgeIndex != -1 else None

    @property
    def _curve_2d(self):
        if self._Brep:
            return self._Brep.Curve2D[self.CurveIndex] # pylint: disable=no-member

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
        return [self.EdgeIndex,
        self.StartIndex,
        self.EndIndex,
        self.FaceIndex,
        self.LoopIndex,
        self.CurveIndex,
        self.IsoStatus,
        self.TrimType.value,
        int(self.IsReversed)
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
    serialize_ignore={"Surfaces", "Curve3D", "Curve2D", "Vertices", "Trims", "Edges", "Loops", "Faces"},
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
            child._Brep = self
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
        if not self.Edges:
            return
        value = []
        for edge in self.Edges:
            value.extend(edge.to_list())
        return value

    @EdgesValue.setter
    def EdgesValue(self, value: List[float]):
        if not value:
            return

        self.Edges = []
        index = 0
        while index < len(value):
            item_count = value[index]
            self.Edges.append(BrepEdge.from_list(value[index + 1 : index + item_count], self))
            index += item_count + 1

    @property
    def LoopsValue(self) -> List[BrepLoop]:
        if not self.Loops:
            return
        value = []
        for loop in self.Loops:
            value.extend(loop.to_list())
        return value

    @LoopsValue.setter
    def LoopsValue(self, value: List[int]):
        if not value:
            return

        self.Loops = []
        index = 0
        while index < len(value):
            item_count = value[index]
            self.Loops.append(BrepLoop.from_list(value[index + 1 : index + item_count], self))
            index += item_count + 1

    @property
    def FacesValue(self) -> List[int]:
        if not self.Faces:
            return
        value = []
        for face in self.Faces:
            value.extend(face.to_list())
        return value

    @FacesValue.setter
    def FacesValue(self, value: List[int]):
        if not value:
            return

        self.Faces = []
        index = 0
        while index < len(value):
            item_count = value[index]
            self.Faces.append(BrepFace.from_list(value[index + 1 : index + item_count], self))
            index += item_count + 1

    @property
    def SurfacesValue(self) -> List[float]:
        return None if self.Surfaces is None else ObjectArray.from_objects(self.Surfaces).data

    @SurfacesValue.setter
    def SurfacesValue(self, value: List[float]):
        if not value:
            return

        self.Surfaces = ObjectArray.decode_data(value, Surface.from_list)

    @property
    def Curve3DValues(self) -> List[float]:
        return None if self.Curve3D is None else CurveArray.from_curves(self.Curve3D).data

    @Curve3DValues.setter
    def Curve3DValues(self, value: List[float]):
        crv_array = CurveArray()
        crv_array.data = value
        self.Curve3D = crv_array.to_curves()

    @property
    def Curve2DValues(self) -> List[Base]:
        return None if self.Curve2D is None else CurveArray.from_curves(self.Curve2D).data

    @Curve2DValues.setter
    def Curve2DValues(self, value: List[float]):
        crv_array = CurveArray()
        crv_array.data = value
        self.Curve2D = crv_array.to_curves()

    @property
    def VerticesValue(self) -> List[Point]:
        if self.Vertices is None:
            return None
        encoded_unit = get_encoding_from_units(self.Vertices[0].units)
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

    @property
    def TrimsValue(self) -> List[float]:
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

        self.Trims = [BrepTrim.from_list(value[i : i + 9], self) for i in range(0, len(value), 9)]



BrepEdge.update_forward_refs()
BrepLoop.update_forward_refs()
BrepTrim.update_forward_refs()
BrepFace.update_forward_refs()
