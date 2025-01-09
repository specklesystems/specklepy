from typing import Any, Dict, List
from specklepy.objects.base import Base
from specklepy.objects.interfaces import IDataObject, IGisObject


class DataObject(
    Base,
    IDataObject,
    speckle_type="Objects.Data.DataObject",
    detachable={"displayValue"},
):
    name: str
    properties: Dict[str, Any]
    displayValue: List[Base]

    def __init__(self, *, name, properties, displayValue, application_id=None):
        super().__init__()
        self.name = name
        self.properties = properties
        self.displayValue = displayValue

        if application_id:
            self.applicationId = application_id


class QgisObject(DataObject, IGisObject, speckle_type="Objects.Data.QgisObject"):

    units: str

    @property
    def type(self) -> str:
        pass

    @property
    def properties(self) -> str:
        pass

    @property
    def displayValue(self) -> List[Base]:
        pass

    @property
    def name(self) -> str:
        pass

    def __init__(self, *, name, properties, displayValue, type, units, application_id):
        super().__init__(
            name=name,
            properties=properties,
            displayValue=displayValue,
            application_id=application_id,
        )
        self.type = type
        self.units = units
