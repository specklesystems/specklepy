from dataclasses import dataclass
from enum import Enum
from unicodedata import name

# following imports seem to be unnecessary, but they need to stay 
# to not break the scripts using these functions as non-core
from specklepy.core.api.host_applications import (HostApplication, HostAppVersion,
                                                  get_host_app_from_string, 
                                                  RHINO,GRASSHOPPER,REVIT,DYNAMO,UNITY,GSA,
                                                  CIVIL,AUTOCAD,MICROSTATION,OPENROADS,
                                                  OPENRAIL,OPENBUILDINGS,ETABS,SAP2000,CSIBRIDGE,
                                                  SAFE,TEKLASTRUCTURES,DXF,EXCEL,UNREAL,POWERBI,
                                                  BLENDER,QGIS,ARCGIS,SKETCHUP,ARCHICAD,TOPSOLID,
                                                  PYTHON,NET,OTHER)

if __name__ == "__main__":
    print(HostAppVersion.v)
