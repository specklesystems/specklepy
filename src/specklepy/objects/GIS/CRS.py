from typing import Optional

from specklepy.objects.base import Base


class CRS(Base, speckle_type="Objects.GIS.CRS"):
    """A Coordinate Reference System reconstructable from WKT string"""

    name: str
    authority_id: Optional[str]
    wkt: str
    units_native: Optional[str]
    offset_x: Optional[float]
    offset_y: Optional[float]
    rotation: Optional[float]

    def __init__(
        self,
        name: str,
        authority_id: Optional[str],
        wkt: str,
        units_native: Optional[str] = None,
        offset_x: Optional[float] = None,
        offset_y: Optional[float] = None,
        rotation: Optional[float] = None,
    ) -> None:
        super().__init__(
            name=name,
        )
