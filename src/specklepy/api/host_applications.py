from dataclasses import dataclass
from enum import Enum
from unicodedata import name

# following imports seem to be unnecessary, but they need to stay
# to not break the scripts using these functions as non-core
from specklepy.core.api.host_applications import (
    ARCGIS,
    ARCHICAD,
    AUTOCAD,
    BLENDER,
    CIVIL,
    CSIBRIDGE,
    DXF,
    DYNAMO,
    ETABS,
    EXCEL,
    GRASSHOPPER,
    GSA,
    MICROSTATION,
    NET,
    OPENBUILDINGS,
    OPENRAIL,
    OPENROADS,
    OTHER,
    POWERBI,
    PYTHON,
    QGIS,
    REVIT,
    RHINO,
    SAFE,
    SAP2000,
    SKETCHUP,
    TEKLASTRUCTURES,
    TOPSOLID,
    UNITY,
    UNREAL,
    HostApplication,
    HostAppVersion,
    _app_name_host_app_mapping,
    get_host_app_from_string,
)

if __name__ == "__main__":
    print(HostAppVersion.v)
