from typing import List

from specklepy.objects.base import Base
from specklepy.objects.geometry import Mesh, Point, Polyline
from specklepy.objects.GIS.geometry import PolygonGeometry


class GisNonGeometricFeature(Base, speckle_type="Objects.GIS.GisNonGeometricFeature"):
    """GIS Table feature"""

    attributes: Base


class GisPointFeature(
    Base,
    detachable={"displayValue"},
    speckle_type="Objects.GIS.GisPointFeature",
):
    """Gis Point Feature"""

    attributes: Base
    displayValue: List[Point]

    @property
    def geometry(self) -> List[Point]:
        return self.displayValue


class GisPolylineFeature(
    Base,
    detachable={"displayValue"},
    speckle_type="Objects.GIS.GisPolylineFeature",
):
    """Gis Polyline Feature"""

    attributes: Base
    displayValue: List[Polyline]

    @property
    def geometry(self) -> List[Polyline]:
        return self.displayValue


class GisPolygonFeature(
    Base,
    detachable={"displayValue", "geometry"},
    speckle_type="Objects.GIS.GisPolygonFeature",
):
    """Gis Polygon Feature"""

    attributes: Base
    displayValue: List[Mesh]
    geometry: List[PolygonGeometry]


class GisMultipatchFeature(
    Base,
    detachable={"displayValue", "geometry"},
    speckle_type="Objects.GIS.GisMultipatchFeature",
):
    """Gis Multipatch Feature"""

    attributes: Base
    displayValue: List[Mesh]
    geometry: List[Base]  # GisMultipatchGeometry or PolygonGeometry3d
