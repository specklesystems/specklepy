from __future__ import annotations

from typing import List, Optional, Any

from pydantic import BaseModel
from pydantic.main import Extra


class Base(BaseModel):
    id: Optional[str] = None
    totalChildrenCount: Optional[int] = None
    applicationId: Optional[str] = None
    speckle_type: Optional[str] = None

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

    class Config:
        extra = Extra.allow