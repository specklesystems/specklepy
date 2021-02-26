from .base import Base
from typing import Any, List

GEOMETRY = "Objects.Geometry."


class Interval(Base, speckle_type="Objects.Primitive.Interval"):
    start: float = 0
    end: float = 0

    def length(self):
        return abs(self.start - self.end)


class Point(Base, speckle_type=GEOMETRY + "Point"):
    x: float = 0
    y: float = 0
    z: float = 0

    def __init__(self, x: float = 0, y: float = 0, z: float = 0, **data: Any) -> None:
        super().__init__(**data)
        self.x, self.y, self.z = x, y, z

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(x: {self.x}, y: {self.y}, z: {self.z}, id: {self.id}, speckle_type: {self.speckle_type})"


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


class Polyline(Base, speckle_type=GEOMETRY + "Polyline"):
    value: List[float] = None
    closed: bool = None
    domain: Interval = None
    bbox: Box = None
    area: float = None
    length: float = None

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._chunkable.update({"value": 20000})

    @classmethod
    def from_points(cls, points: List[Point]):
        polyline = cls()
        polyline.units = points[0].units
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
        return [Point(v, next(values), next(values), units=self.units) for v in values]


class Curve(Base, speckle_type=GEOMETRY + "Curve"):
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

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._chunkable.update({"points": 20000, "weights": 20000, "knots": 20000})

    def as_points(self) -> List[Point]:
        """Converts the `value` attribute to a list of Points"""
        if not self.points:
            return

        if len(self.points) % 3:
            raise ValueError("Points array malformed: length%3 != 0.")

        values = iter(self.points)
        return [Point(v, next(values), next(values), units=self.units) for v in values]


class Polycurve(Base, speckle_type=GEOMETRY + "Polycurve"):
    segments: List[Base] = []
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


class Mesh(Base, speckle_type=GEOMETRY + "Mesh"):
    vertices: List[float] = None
    faces: List[int] = None
    colors: List[int] = None
    textureCoordinates: List[float] = None
    bbox: Box = None
    area: float = None
    volume: float = None

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self._chunkable.update(
            {
                "vertices": 2000,
                "faces": 2000,
                "colors": 2000,
                "textureCoordinates": 2000,
            }
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
