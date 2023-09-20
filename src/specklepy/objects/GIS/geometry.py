from typing import Optional, Union, List
from specklepy.objects.geometry import (
    Point,
    Line,
    Polyline,
    Circle,
    Arc,
    Polycurve,
    Mesh,
)
from specklepy.objects.base import Base


class GisPolygonGeometry(
    Base, speckle_type="Objects.GIS.PolygonGeometry", detachable={"displayValue"}
):
    """GIS Polygon Geometry"""

    boundary: Optional[Union[Polyline, Arc, Line, Circle, Polycurve]] = None
    voids: Optional[List[Union[Polyline, Arc, Line, Circle, Polycurve]]] = None
    displayValue: Optional[List[Mesh]] = None


class GisPolygonElement(Base, speckle_type="Objects.GIS.PolygonElement"):
    """GIS Polygon element"""

    geometry: Optional[List[GisPolygonGeometry]] = None
    attributes: Optional[Base] = None


class GisLineElement(Base, speckle_type="Objects.GIS.LineElement"):
    """GIS Polyline element"""

    geometry: Optional[List[Union[Polyline, Arc, Line, Circle, Polycurve]]] = (None,)
    attributes: Optional[Base] = (None,)


class GisPointElement(Base, speckle_type="Objects.GIS.PointElement"):
    """GIS Point element"""

    geometry: Optional[List[Point]] = (None,)
    attributes: Optional[Base] = (None,)


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


class GisNonGeometryElement(Base, speckle_type="Objects.GIS.NonGeometryElement"):
    """GIS Table feature"""

    attributes: Optional[Base] = None
