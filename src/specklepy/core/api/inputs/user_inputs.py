from typing import Optional

from pydantic import BaseModel


class UserUpdateInput(BaseModel):
    avatar: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    name: Optional[str] = None
