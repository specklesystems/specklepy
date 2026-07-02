from dataclasses import dataclass
from enum import Enum
from unicodedata import name


class HostAppVersion(Enum):
    v = "v"
    v6 = "v6"
    v7 = "v7"
    v2019 = "v2019"
    v2020 = "v2020"
    v2021 = "v2021"
    v2022 = "v2022"
    v2023 = "v2023"
    v2024 = "v2024"
    v2025 = "v2025"
    vSandbox = "vSandbox"
    vRevit = "vRevit"
    vRevit2021 = "vRevit2021"
    vRevit2022 = "vRevit2022"
    vRevit2023 = "vRevit2023"
    vRevit2024 = "vRevit2024"
    vRevit2025 = "vRevit2025"
    v25 = "v25"
    v26 = "v26"

    def __repr__(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass
class HostApplication:
    name: str
    slug: str

    def get_version(self, version: HostAppVersion) -> str:
        return f"{name.replace(' ', '')}{str(version).strip('v')}"


RHINO = HostApplication("Rhino", "rhino")
GRASSHOPPER = HostApplication("Grasshopper", "grasshopper")
REVIT = HostApplication("Revit", "revit")
DYNAMO = HostApplication("Dynamo", "dynamo")
UNITY = HostApplication("Unity", "unity")
GSA = HostApplication("GSA", "gsa")
CIVIL = HostApplication("Civil 3D", "civil3d")
AUTOCAD = HostApplication("AutoCAD", "autocad")
MICROSTATION = HostApplication("MicroStation", "microstation")
OPENROADS = HostApplication("OpenRoads", "openroads")
OPENRAIL = HostApplication("OpenRail", "openrail")
OPENBUILDINGS = HostApplication("OpenBuildings", "openbuildings")
ETABS = HostApplication("ETABS", "etabs")
SAP2000 = HostApplication("SAP2000", "sap2000")
CSIBRIDGE = HostApplication("CSIBridge", "csibridge")
SAFE = HostApplication("SAFE", "safe")
TEKLASTRUCTURES = HostApplication("Tekla Structures", "teklastructures")
DXF = HostApplication("DXF Converter", "dxf")
EXCEL = HostApplication("Excel", "excel")
UNREAL = HostApplication("Unreal", "unreal")
POWERBI = HostApplication("Power BI", "powerbi")
BLENDER = HostApplication("Blender", "blender")
QGIS = HostApplication("QGIS", "qgis")
ARCGIS = HostApplication("ArcGIS", "arcgis")
SKETCHUP = HostApplication("SketchUp", "sketchup")
ARCHICAD = HostApplication("Archicad", "archicad")
TOPSOLID = HostApplication("TopSolid", "topsolid")
PYTHON = HostApplication("Python", "python")
NET = HostApplication(".NET", "net")
OTHER = HostApplication("Other", "other")

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
