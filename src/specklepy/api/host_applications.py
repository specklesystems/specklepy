from dataclasses import dataclass
from enum import Enum
from unicodedata import name

# following imports seem to be unnecessary, but they need to stay 
# to not break the scripts using these functions as non-core
from specklepy.core.api.host_applications import (HostAppVersion,
                                                  RHINO,GRASSHOPPER,REVIT,DYNAMO,UNITY,GSA,
                                                  CIVIL,AUTOCAD,MICROSTATION,OPENROADS,
                                                  OPENRAIL,OPENBUILDINGS,ETABS,SAP2000,CSIBRIDGE,
                                                  SAFE,TEKLASTRUCTURES,DXF,EXCEL,UNREAL,POWERBI,
                                                  BLENDER,QGIS,ARCGIS,SKETCHUP,ARCHICAD,TOPSOLID,
                                                  PYTHON,NET,OTHER)

@dataclass
class HostApplication:
    name: str
    slug: str

    def get_version(self, version: HostAppVersion) -> str:
        return f"{name.replace(' ', '')}{str(version).strip('v')}"

_app_name_host_app_mapping = {
    "dynamo": DYNAMO,
    "revit": REVIT,
    "autocad": AUTOCAD,
    "civil": CIVIL,
    "rhino": RHINO,
    "grasshopper": GRASSHOPPER,
    "unity": UNITY,
    "gsa": GSA,
    "microstation": MICROSTATION,
    "openroads": OPENROADS,
    "openrail": OPENRAIL,
    "openbuildings": OPENBUILDINGS,
    "etabs": ETABS,
    "sap": SAP2000,
    "csibridge": CSIBRIDGE,
    "safe": SAFE,
    "teklastructures": TEKLASTRUCTURES,
    "dxf": DXF,
    "excel": EXCEL,
    "unreal": UNREAL,
    "powerbi": POWERBI,
    "blender": BLENDER,
    "qgis": QGIS,
    "arcgis": ARCGIS,
    "sketchup": SKETCHUP,
    "archicad": ARCHICAD,
    "topsolid": TOPSOLID,
    "python": PYTHON,
    "net": NET,
}

def get_host_app_from_string(app_name: str) -> HostApplication:
    app_name = app_name.lower().replace(" ", "")
    for partial_app_name, host_app in _app_name_host_app_mapping.items():
        if partial_app_name in app_name:
            return host_app
    return HostApplication(app_name, app_name)


if __name__ == "__main__":
    print(HostAppVersion.v)
