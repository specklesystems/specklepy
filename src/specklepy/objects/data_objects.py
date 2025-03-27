from dataclasses import dataclass, field
from typing import Dict, List

from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.base import Base
from specklepy.objects.interfaces import IDataObject, IGisObject, IHasUnits


@dataclass(kw_only=True)
class DataObject(
    Base,
    IDataObject,
    speckle_type="Objects.Data.DataObject",
    detachable={"displayValue"},
):
    name: str
    properties: Dict[str, object]
    displayValue: List[Base]
    _name: str = field(repr=False, init=False)
    _properties: Dict[str, object] = field(repr=False, init=False)
    _displayValue: List[Base] = field(repr=False, init=False)

    @property
    def name(self) -> str:
        return self._name

    @property
    def properties(self) -> Dict[str, object]:
        return self._properties

    @property
    def displayValue(self) -> List[Base]:
        return self._displayValue

    @name.setter
    def name(self, value: str):
        if isinstance(value, str):
            self._name = value
        else:
            raise SpeckleException(
                f"'name' value should be string, received {type(value)}"
            )

    @properties.setter
    def properties(self, value: dict):
        if isinstance(value, dict):
            self._properties = value
        else:
            raise SpeckleException(
                f"'properties' value should be Dict, received {type(value)}"
            )

    @displayValue.setter
    def displayValue(self, value: list):
        if isinstance(value, list):
            self._displayValue = value
        else:
            raise SpeckleException(
                f"'displayValue' value should be List, received {type(value)}"
            )


@dataclass(kw_only=True)
class QgisObject(
    DataObject, IGisObject, IHasUnits, speckle_type="Objects.Data.QgisObject"
):
    type: str
    _type: str = field(repr=False, init=False)

    @property
    def type(self) -> str:
        return self._type

    @type.setter
    def type(self, value: str):
        if isinstance(value, str):
            self._type = value
        else:
            raise SpeckleException(
                f"'type' value should be string, received {type(value)}"
            )
