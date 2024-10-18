from typing import Optional, Sequence
from pydantic import BaseModel

from specklepy.core.api.models import ProjectVisibility


class ProjectCommentsFilter(BaseModel):
    includeArchived: Optional[bool]
    loadedVersionsOnly: Optional[bool]
    resourceIdString: Optional[str]


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
    contributors: Optional[Sequence[str]]
    excludeIds: Optional[Sequence[str]]
    ids: Optional[Sequence[str]]
    onlyWithVersions: Optional[bool]
    search: Optional[str]
    sourceApps: Sequence[str]


class ProjectModelsTreeFilter(BaseModel):
    contributors: Optional[Sequence[str]]
    search: Optional[str]
    sourceApps: Sequence[str]


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
