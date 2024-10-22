"""Builtin Speckle object kit."""

from specklepy.objects.GIS.CRS import CRS
from specklepy.objects.GIS.geometry import (
    PolygonGeometry,
    PolygonGeometry3d,
    GisLineElement,
    GisPointElement,
    GisPolygonElement,
    GisRasterElement,
)
from specklepy.objects.GIS.layers import RasterLayer, VectorLayer
from specklepy.objects.GIS.features import (
    GisPointFeature,
    GisPolylineFeature,
    GisPolygonFeature,
    GisMultipatchFeature,
    GisNonGeometricFeature,
)

__all__ = [
    "VectorLayer",
    "RasterLayer",
    "PolygonGeometry",
    "PolygonGeometry3d",
    "GisPolygonElement",
    "GisLineElement",
    "GisPointElement",
    "GisRasterElement",
    "CRS",
    "GisPointFeature",
    "GisPolylineFeature",
    "GisPolygonFeature",
    "GisMultipatchFeature",
    "GisNonGeometricFeature",
]
