from typing import Optional
from specklepy.objects import Base


class CRS(Base, speckle_type="Objects.GIS.CRS"):
    """A Coordinate Reference System stored in wkt format"""

    def __init__(
        self, 
        name: Optional[str] = None, 
        authority_id: Optional[str] = None, 
        wkt: Optional[str] = None, 
        units: Optional[str] = None, 
        **kwargs
    ) -> None:
        super().__init__(**kwargs)

        self.name = name 
        self.authority_id = authority_id 
        self.wkt = wkt 
        self.units = units or "m"

