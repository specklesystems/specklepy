from .base import Base
from typing import Any, List

GEOMETRY = "Objects.Geometry."


class Interval(Base, speckle_type="Objects.Primitive.Interval"):
    start: float = 0.0
    end: float = 0.0

    def length(self):
        return abs(self.start - self.end)


class Point(Base, speckle_type=GEOMETRY + "Point"):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x: {self.x}, y: {self.y}, z: {self.z}, id: {self.id}, speckle_type: {self.speckle_type})"

    @classmethod
    def from_coords(x: float = 0.0, y: float = 0.0, z: float = 0.0):
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


class Circle(Base, speckle_type=GEOMETRY + "Circle"):
    radius: float = None
    plane: Plane = None
    domain: Interval = None
    bbox: Box = None
    area: float = None
    length: float = None


class Ellipse(Base, speckle_type=GEOMETRY + "Ellipse"):
    firstRadius: float = None
    secondRadius: float = None
    plane: Plane = None
    domain: Interval = None
    trimDomain: Interval = None
    bbox: Box = None
    area: float = None
    length: float = None


class Polyline(Base, speckle_type=GEOMETRY + "Polyline", chunkable={"value": 20000}):
    value: List[float] = None
    closed: bool = None
    domain: Interval = None
    bbox: Box = None
    area: float = None
    length: float = None

    @classmethod
    def from_points(cls, points: List[Point]):
        polyline = cls()
        polyline.units = points[0].units
        polyline.value = []
        for point in points:
            polyline.value.extend([point.x, point.y, point.z])
        return polyline

    # @property
    # def value(self) -> List[float]:
    #     return self._value

    # @value.setter
    # def value(self, coords) -> None:
    #     if len(coords) % 3:
    #         coords.extend([0] * (3 - len(coords) % 3))
    #     self._value = coords

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


class Polycurve(Base, speckle_type=GEOMETRY + "Polycurve"):
    segments: List[Base] = None
    domain: Interval = None
    closed: bool = None
    bbox: Box = None
    area: float = None
    length: float = None


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


class Surface(Base, speckle_type=GEOMETRY + "Surface"):
    degreeU: int = None
    degreeV: int = None
    rational: bool = None
    area: float = None
    pointData: List[float] = None
    countU: int = None
    countV: int = None
    bbox: Box = None


class BrepFace(Base, speckle_type=GEOMETRY + "BrepFace"):
    _Brep: "Brep" = None
    SurfaceIndex: int = None
    LoopIndices: List[int] = None
    OuterLoopIndex: int = None
    OrientationReversed: bool = None

    @property
    def _outer_loop(self):
        return self._Brep.Loops[self.OuterLoopIndex]

    @property
    def _surface(self):
        return self._Brep.Surfaces[self.SurfaceIndex]

    @property
    def _loops(self):
        if self.LoopIndices:
            return [self._Brep.Loops[i] for i in self.LoopIndices]


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
            return [self._Brep.Trims[i] for i in self.TrimIndices]

    @property
    def _curve(self):
        return self._Brep.Curve3D[self.Curve3dIndex]


class BrepLoop(Base, speckle_type=GEOMETRY + "BrepLoop"):
    _Brep: "Brep" = None
    FaceIndex: int = None
    TrimIndices: List[int] = None
    Type: str = None

    @property
    def _face(self):
        return self._Brep.Faces[self.FaceIndex]

    @property
    def _trims(self):
        if self.TrimIndices:
            return [self._Brep.Trims[i] for i in self.TrimIndices]


class BrepTrim(Base, speckle_type=GEOMETRY + "BrepTrim"):
    _Brep: "Brep" = None
    EdgeIndex: int = None
    StartIndex: int = None
    EndIndex: int = None
    FaceIndex: int = None
    LoopIndex: int = None
    CurveIndex: int = None
    IsoStatus: int = None
    TrimType: str = None
    IsReversed: bool = None
    Domain: Interval = None

    @property
    def _face(self):
        return self._Brep.Faces[self.FaceIndex]

    @property
    def _loop(self):
        return self._Brep.Loops[self.LoopIndex]

    @property
    def _edge(self):
        return self._Brep.Edges[self.EdgeIndex] if self.EdgeIndex != -1 else None

    @property
    def _curve_2d(self):
        return self._Brep.Curve2D[self.CurveIndex]


class Brep(
    Base,
    speckle_type=GEOMETRY + "Brep",
    chunkable={
        "Surfaces": 200,
        "Curve3D": 200,
        "Curve2D": 200,
        "Vertices": 5000,
        "Edges": 5000,
        "Loops": 5000,
        "Trims": 5000,
        "Faces": 5000,
    },
    detachable={"displayValue"},
):
    provenance: str = None
    bbox: Box = None
    area: float = None
    volume: float = None
    displayValue: Mesh = None
    Surfaces: List[Surface] = None
    Curve3D: List[Base] = None
    Curve2D: List[Base] = None
    Vertices: List[Point] = None
    Edges: List[BrepEdge] = None
    Loops: List[BrepLoop] = None
    Trims: List[BrepTrim] = None
    Faces: List[BrepFace] = None
    IsClosed: bool = None
    Orientation: int = None

    def __setattr__(self, name: str, value: Any) -> None:
        if not value:
            return
        if name in {"Edges", "Loops", "Trims", "Faces"}:
            for val in value:
                val._Brep = self
        super().__setattr__(name, value)


BrepEdge.update_forward_refs()
BrepLoop.update_forward_refs()
BrepTrim.update_forward_refs()
BrepFace.update_forward_refs()
