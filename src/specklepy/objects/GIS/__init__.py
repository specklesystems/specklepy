"""Builtin Speckle object kit."""

from specklepy.objects.GIS.CRS import CRS
from specklepy.objects.GIS.features import (
    GisMultipatchFeature,
    GisNonGeometricFeature,
    GisPointFeature,
    GisPolygonFeature,
    GisPolylineFeature,
)
from specklepy.objects.GIS.geometry import (
    GisLineElement,
    GisPointElement,
    GisPolygonElement,
    GisPolygonGeometry,
    GisRasterElement,
    PolygonGeometry,
    PolygonGeometry3d,
    GisMultipatchGeometry,
)
from specklepy.objects.GIS.layers import RasterLayer, VectorLayer

__all__ = [
    "VectorLayer",
    "RasterLayer",
    "GisPolygonGeometry",
    "PolygonGeometry",
    "PolygonGeometry3d",
    "GisMultipatchGeometry",
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
