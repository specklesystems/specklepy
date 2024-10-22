from typing import List, Optional, Union

from deprecated import deprecated

from specklepy.objects.base import Base
from specklepy.objects.geometry import (
    Arc,
    Circle,
    Line,
    Mesh,
    Point,
    Polycurve,
    Polyline,
)


class PolygonGeometry(Base, speckle_type="Objects.GIS.PolygonGeometry"):
    """GIS Polygon Geometry"""

    boundary: Polyline
    voids: List[Polyline]

    def __init__(
        self,
        units: str,
        boundary: Polyline,
        voids: Optional[List[Polyline]] = None,
    ) -> None:
        super().__init__(units=units)
        self.boundary = boundary
        self.voids = voids or []


GisPolygonGeometry = PolygonGeometry


class PolygonGeometry3d(
    PolygonGeometry,
    speckle_type="Objects.GIS.PolygonGeometry3d",
):
    """GIS Polygon3d Geometry"""

    def __init__(
        self,
        units: str,
        boundary: Polyline,
        voids: Optional[List[Polyline]] = None,
    ) -> None:
        super().__init__(units=units, boundary=boundary, voids=voids)


class GisMultipatchGeometry(
    Base,
    speckle_type="Objects.GIS.GisMultipatchGeometry",
):
    """GIS Polygon3d Geometry"""

    def __init__(
        self,
        units: str,
        faces: List[int],
        vertices: List[float],
        colors: Optional[List[int]],
    ) -> None:
        super().__init__(units=units)
        self.faces = faces
        self.vertices = vertices
        self.colors = colors or []


@deprecated(version="2.20", reason="Replaced with GisPolygonFeature")
class GisPolygonElement(Base, speckle_type="Objects.GIS.PolygonElement"):
    """GIS Polygon element"""

    geometry: Optional[List[PolygonGeometry]] = None
    attributes: Optional[Base] = None


@deprecated(version="2.20", reason="Replaced with GisPolyineFeature")
class GisLineElement(Base, speckle_type="Objects.GIS.LineElement"):
    """GIS Polyline element"""

    geometry: Optional[List[Union[Polyline, Arc, Line, Circle, Polycurve]]] = None
    attributes: Optional[Base] = None


@deprecated(version="2.20", reason="Replaced with GisPointFeature")
class GisPointElement(Base, speckle_type="Objects.GIS.PointElement"):
    """GIS Point element"""

    geometry: Optional[List[Point]] = None
    attributes: Optional[Base] = None


class GisRasterElement(
    Base, speckle_type="Objects.GIS.RasterElement", detachable={"displayValue"}
):
    """GIS Raster element"""

    band_count: Optional[int] = None
    band_names: Optional[List[str]] = None
    x_origin: Optional[float] = None
    y_origin: Optional[float] = None
    x_size: Optional[int] = None
    y_size: Optional[int] = None
    x_resolution: Optional[float] = None
    y_resolution: Optional[float] = None
    noDataValue: Optional[List[float]] = None
    displayValue: Optional[List[Mesh]] = None


class GisTopography(
    GisRasterElement,
    speckle_type="Objects.GIS.GisTopography",
    detachable={"displayValue"},
):
    """GIS Raster element with 3d Topography representation"""


@deprecated(version="2.20", reason="Replaced with GisNonGeometricFeature")
class GisNonGeometryElement(Base, speckle_type="Objects.GIS.NonGeometryElement"):
    """GIS Table feature"""

    attributes: Optional[Base] = None
