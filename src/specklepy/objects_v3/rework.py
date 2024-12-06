from abc import ABCMeta, abstractmethod
from specklepy.objects.base import Base
from dataclasses import dataclass


b = Base("asdf", 10, None)


@dataclass
class IBase(Base, speckle_type="IBase", metaclass=ABCMeta):
    pass


@dataclass(kw_only=True)
class IRhino(IBase, speckle_type="IRhino", metaclass=ABCMeta):
    rhino_name: str

    @abstractmethod
    def __repr__(self) -> str:
        return super().__repr__()


@dataclass(kw_only=True)
class IRevit(Base, speckle_type="IRevit", metaclass=ABCMeta):
    revit_name: str

    @abstractmethod
    def __repr__(self) -> str:
        return super().__repr__()


class Point(Base, speckle_type="Objects.Geometry.Point_V3"):

    def say_foo(self):
        print("foo from point")

    def __init__(
        self,
        *,
        x: float,
        y: float,
        z: float,
        **kwargs,
    ) -> None:
        self.x = x
        self.y = y
        self.z = z
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(x: {self.x}, y: {self.y}, z: {self.z}, id:"
            f" {self.id}, speckle_type: {self.speckle_type})"
        )

    @classmethod
    def from_list(cls, args: list[float]) -> "Point":
        """
        Create a new Point from a list of three floats
        representing the x, y, and z coordinates
        """
        return cls(x=args[0], y=args[1], z=args[2])

    def to_list(self) -> list[float]:
        return [self.x, self.y, self.z]

    @classmethod
    def from_coords(cls, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        """Create a new Point from x, y, and z values"""
        pt = Point()
        pt.x, pt.y, pt.z = x, y, z
        return pt


class Foo(Point, IRhino, speckle_type="Foo"):

    def __init__(
        self,
        *,
        x: float,
        y: float,
        z: float | None = None,
        rhino_name: str,
        # applicationId: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(x=x, y=y, z=z, rhino_name=rhino_name, **kwargs)

    pass


@dataclass(kw_only=True)
class ThisWouldBeNice(Point, IRhino, speckle_type="Nice"):
    x: float
    y: float
    z: float = 0.0


r = IRhino(rhino_name="asdf")

t = ThisWouldBeNice(x=1, y=0, rhino_name="asdf")
print(ThisWouldBeNice.mro())
print(t)
