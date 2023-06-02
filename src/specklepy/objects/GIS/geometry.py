
from typing import Optional, Union, List 
from specklepy.objects.geometry import Point, Line, Polyline, Circle, Arc, Polycurve, Mesh 
from specklepy.objects import Base
from deprecated import deprecated

class GisPolygonGeometry(Base, speckle_type="Objects.GIS.PolygonGeometry", detachable={"displayValue"}):
    """GIS Polygon Geometry"""
    
    def __init__(
        self, 
        boundary: Optional[Union[Polyline, Arc, Line, Circle, Polycurve]] = None, 
        voids: Optional[List[Union[Polyline, Arc, Line, Circle, Polycurve]] ] = None, 
        displayValue: Optional[List[Mesh]] = None, 
        units: Optional[str] = None, 
        **kwargs
    ) -> None:
        super().__init__(**kwargs)

        self.boundary = boundary
        self.voids = voids
        self.displayValue = displayValue 
        self.units = units or "m"

class GisPolygonElement(Base, speckle_type="Objects.GIS.PolygonElement"):
    """GIS Polygon element"""
       
    def __init__(
        self, 
        geometry: Optional[List[GisPolygonGeometry]] = None,
        attributes: Optional[Base] = None,
        units: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)

        self.geometry = geometry
        self.attributes = attributes 
        self.units = units or "m"

class GisLineElement(Base, speckle_type="Objects.GIS.LineElement"):
    """GIS Polyline element"""
        
    def __init__(
        self, 
        geometry: Optional[List[Union[Polyline, Arc, Line, Circle, Polycurve]]] = None,
        attributes: Optional[Base] = None,
        units: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        
        self.geometry = geometry
        self.attributes = attributes 
        self.units = units or "m"

class GisPointElement(Base, speckle_type="Objects.GIS.PointElement"):
    """GIS Point element"""
    
    def __init__(
        self, 
        geometry: Optional[List[Point]] = None,
        attributes: Optional[Base] = None,
        units: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        
        self.geometry = geometry
        self.attributes = attributes 
        self.units = units or "m"

class GisRasterElement(Base, speckle_type="Objects.GIS.RasterElement", detachable={"displayValue"}):
    """GIS Raster element"""

    def __init__(
        self, 
        band_count: Optional[int] = None,
        band_names: Optional[List[str]] = None,
        x_origin: Optional[float] = None,
        y_origin: Optional[float] = None,
        x_size: Optional[int] = None,
        y_size: Optional[int] = None,
        x_resolution: Optional[float] = None,
        y_resolution: Optional[float] = None,
        noDataValue: Optional[List[float]] = None,
        displayValue: Optional[List[Mesh]] = None, 
        units: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        
        self.band_count = band_count
        self.band_names = band_names
        self.x_origin = x_origin
        self.y_origin = y_origin
        self.x_size = x_size
        self.y_size = y_size
        self.x_resolution = x_resolution
        self.y_resolution = y_resolution
        self.noDataValue = noDataValue
        self.displayValue = displayValue
        self.units = units or "m"

