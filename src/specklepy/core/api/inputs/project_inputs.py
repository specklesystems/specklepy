from typing import Optional, Sequence

from pydantic import BaseModel

from specklepy.core.api.enums import ProjectVisibility


class ProjectCreateInput(BaseModel):
    name: Optional[str]
    description: Optional[str]
    visibility: Optional[ProjectVisibility]


class ProjectInviteCreateInput(BaseModel):
    email: Optional[str]
    role: Optional[str]
    serverRole: Optional[str]
    userId: Optional[str]


class ProjectInviteUseInput(BaseModel):
    accept: bool
    projectId: str
    token: str


class ProjectModelsFilter(BaseModel):
    contributors: Optional[Sequence[str]] = None
    excludeIds: Optional[Sequence[str]] = None
    ids: Optional[Sequence[str]] = None
    onlyWithVersions: Optional[bool] = None
    search: Optional[str] = None
    sourceApps: Optional[Sequence[str]] = None


class ProjectUpdateInput(BaseModel):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    allowPublicComments: Optional[bool] = None
    visibility: Optional[ProjectVisibility] = None


class ProjectUpdateRoleInput(BaseModel):
    userId: str
    projectId: str
    role: Optional[str]


class UserProjectsFilter(BaseModel):
    search: str
    onlyWithRole: Optional[Sequence[str]] = None
