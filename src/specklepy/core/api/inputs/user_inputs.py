from typing import Optional, Sequence

from pydantic import BaseModel


class UserUpdateInput(BaseModel):
    avatar: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    name: Optional[str] = None


class UserProjectsFilter(BaseModel):
    search: str
    onlyWithRoles: Optional[Sequence[str]] = None
