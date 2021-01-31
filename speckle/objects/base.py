from pydantic import BaseModel
from pydantic.main import Extra
from typing import Dict, List, Optional, Any
from speckle.transports.memory import MemoryTransport
from speckle.logging.exceptions import SpeckleException
from speckle.objects.units import get_units_from_string

PRIMITIVES = (int, float, str, bool)


class Base(BaseModel):
    id: Optional[str] = None
    totalChildrenCount: Optional[int] = None
    applicationId: Optional[str] = None
    speckle_type: Optional[str] = "Base"
    _units: str = "m"
    _chunkable: Dict[str, int] = {}  # dict of chunkable props and their max chunk size
    _chunk_size_default: int = 1000
    _detachable: List[str] = []  # list of defined detachable props

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.speckle_type = self.__class__.__name__
        self.__dict__.update(kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id: {self.id}, speckle_type: {self.speckle_type}, totalChildrenCount: {self.totalChildrenCount})"

    def __str__(self) -> str:
        return self.__repr__()

    def __setitem__(self, name: str, value: Any) -> None:
        self.__dict__[name] = value

    def __getitem__(self, name: str) -> Any:
        return self.__dict__[name]

    def __setattr__(self, name, value):
        attr = getattr(self.__class__, name, None)
        if isinstance(attr, property):
            attr.__set__(self, value)
        super().__setattr__(name, value)

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, value: str):
        self._units = get_units_from_string(value)

    def to_dict(self) -> Dict:
        """Convenience method to view the whole base object as a dict"""
        base_dict = self.__dict__
        for key, value in base_dict.items():
            if not value or isinstance(value, PRIMITIVES):
                continue
            else:
                base_dict[key] = self.__dict_helper(value)
        return base_dict

    def __dict_helper(self, obj: Any) -> Any:
        if isinstance(obj, PRIMITIVES):
            return obj
        if isinstance(obj, Base):
            return self.__dict_helper(obj.__dict__)
        if isinstance(obj, (list, set)):
            return [self.__dict_helper(v) for v in obj]
        if isinstance(obj, dict):
            for k, v in obj.items():
                if not v or isinstance(obj, PRIMITIVES):
                    pass
                else:
                    obj[k] = self.__dict_helper(v)
            return obj
        else:
            raise SpeckleException(
                message=f"Could not convert to dict due to unrecognised type: {type(obj)}"
            )

    def get_member_names(self) -> List[str]:
        """Get all of the property names on this object, dynamic or not"""
        return list(self.__dict__.keys())

    def get_typed_member_names(self) -> List[str]:
        """Get all of the names of the defined (typed) properties of this object"""
        return list(self.__fields__.keys())

    def get_dynamic_member_names(self) -> List[str]:
        """Get all of the names of the dynamic properties of this object"""
        return list(set(self.__dict__.keys()) - set(self.__fields__.keys()))

    def get_children_count(self) -> int:
        """Get the total count of children Base objects"""
        parsed = []
        return 1 + self._count_descendants(self, parsed)

    def get_id(self, decompose: bool = False) -> str:
        if self.id and not decompose:
            return self.id
        else:
            from speckle.serialization.base_object_serializer import (
                BaseObjectSerializer,
            )

            serializer = BaseObjectSerializer()
            if decompose:
                serializer.write_transports = [MemoryTransport()]
            return serializer.traverse_base(self)[0]

    def _count_descendants(self, base: "Base", parsed: List) -> int:
        if base in parsed:
            return 0
        parsed.append(base)

        count = 0

        for name, value in base.__dict__.items():
            if name.startswith("@"):
                continue
            else:
                count += self._handle_object_count(value, parsed)

        return count

    def _handle_object_count(self, obj: Any, parsed: List) -> int:
        count = 0
        if obj == None:
            return count
        if isinstance(obj, "Base"):
            count += 1
            count += self._count_descendants(obj, parsed)
            return count
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, "Base"):
                    count += 1
                    count += self._count_descendants(item, parsed)
                else:
                    count += self._handle_object_count(item, parsed)
        elif isinstance(obj, dict):
            for _, value in obj.items():
                if isinstance(value, "Base"):
                    count += 1
                    count += self._count_descendants(value, parsed)
                else:
                    count += self._handle_object_count(value, parsed)
        return count

    class Config:
        extra = Extra.allow


class DataChunk(Base):
    data: List[Any] = []
