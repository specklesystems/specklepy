from typing import Optional

from specklepy.objects.base import Base


class CRS(Base, speckle_type="Objects.GIS.CRS"):
    """A Coordinate Reference System stored in wkt format"""

    name: Optional[str] = None
    authority_id: Optional[str] = None
    wkt: Optional[str] = None
    units_native: Optional[str] = None
    offset_x: Optional[float] = None
    offset_y: Optional[float] = None
    rotation: Optional[float] = None
