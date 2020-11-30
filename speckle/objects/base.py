from __future__ import annotations

from typing import List, Optional, Any

from pydantic import BaseModel
from pydantic.main import Extra


class Base(BaseModel):
    id: Optional[str] = None
    totalChildrenCount: Optional[int] = None
    applicationId: Optional[str] = None
    speckle_type: Optional[str] = None

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.__dict__.update(kwargs)

    def __str__(self) -> str:
        return f"Base(id: {self.id}, speckle_type: {self.speckle_type}, totalChildrenCount: {self.totalChildrenCount})"

    def __setitem__(self, name: str, value: Any) -> None:
        self.__dict__[name] = value

    def __getitem__(self, name: str) -> Any:
        return self.__dict__[name]

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

    def _count_descendants(self, base: Base, parsed: List) -> int:
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
        if isinstance(obj, Base):
            count += 1
            count += self._count_descendants(obj, parsed)
            return count
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, Base):
                    count += 1
                    count += self._count_descendants(item, parsed)
                else:
                    count += self._handle_object_count(item, parsed)
        elif isinstance(obj, dict):
            for _, value in obj.items():
                if isinstance(value, Base):
                    count += 1
                    count += self._count_descendants(value, parsed)
                else:
                    count += self._handle_object_count(value, parsed)
        return count

    class Config:
        extra = Extra.allow