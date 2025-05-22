from dataclasses import dataclass

from specklepy.objects.base import Base
from specklepy.objects.geometry.plane import Plane
from specklepy.objects.interfaces import IHasArea, IHasUnits, IHasVolume
from specklepy.objects.primitive import Interval


@dataclass(kw_only=True)
class Box(Base, IHasUnits, IHasArea, IHasVolume, speckle_type="Objects.Geometry.Box"):
    """
    A 3-dimensional box oriented on a plane.

    This class represents a rectangular prism in 3D space, defined by a base plane and
    three intervals specifying its dimensions along the x, y, and z axes.

    Attributes:
        basePlane: The plane on which the box is oriented
        xSize: The interval defining the box's size along the x-axis
        ySize: The interval defining the box's size along the y-axis
        zSize: The interval defining the box's size along the z-axis

    ```py title="Example"
    from specklepy.objects.geometry.plane import Plane
    from specklepy.objects.geometry.point import Point
    from specklepy.objects.primitive import Interval

    base_plane = Plane(origin=Point(0, 0, 0), normal=Point(0, 0, 1))
    x_size = Interval(start=0, end=10)
    y_size = Interval(start=0, end=5)
    z_size = Interval(start=0, end=3)

    box = Box(basePlane=base_plane, xSize=x_size, ySize=y_size, zSize=z_size)
    ```
    """

    basePlane: Plane
    xSize: Interval
    ySize: Interval
    zSize: Interval

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"basePlane: {self.basePlane}, "
            f"xSize: {self.xSize}, "
            f"ySize: {self.ySize}, "
            f"zSize: {self.zSize}, "
            f"units: {self.units})"
        )

    @property
    def area(self) -> float:
        """Calculates the surface area of the box.

        Returns:
            The total surface area of the box.
        """
        return 2 * (
            self.xSize.length * self.ySize.length
            + self.xSize.length * self.zSize.length
            + self.ySize.length * self.zSize.length
        )

    @property
    def volume(self) -> float:
        """Calculates the volume of the box.

        Returns:
            The volume of the box.
        """
        return self.xSize.length * self.ySize.length * self.zSize.length
