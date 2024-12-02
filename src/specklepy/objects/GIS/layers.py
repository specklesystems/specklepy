from typing import Optional

from specklepy.objects.GIS.CRS import CRS
from specklepy.objects.other import Collection


class GisLayer(
    Collection,
    detachable={"elements"},
    speckle_type="Objects.GIS.GisLayer",
):
    """GIS Vector Layer"""

    # crs: CRS
    units: str
    type: str

    def __init__(
        self,
        # crs: str,
        units: str,
        type: str,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(
            name=name,
        )
