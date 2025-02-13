from typing import Optional, Sequence

from specklepy.core.api.enums import ProjectVisibility
from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel


class ProjectCreateInput(GraphQLBaseModel):
    name: Optional[str]
    description: Optional[str]
    visibility: Optional[ProjectVisibility]


class ProjectInviteCreateInput(GraphQLBaseModel):
    email: Optional[str]
    role: Optional[str]
    server_role: Optional[str]
    userId: Optional[str]


class ProjectInviteUseInput(GraphQLBaseModel):
    accept: bool
    project_id: str
    token: str


class ProjectModelsFilter(GraphQLBaseModel):
    contributors: Optional[Sequence[str]] = None
    exclude_ids: Optional[Sequence[str]] = None
    ids: Optional[Sequence[str]] = None
    only_with_versions: Optional[bool] = None
    search: Optional[str] = None
    source_apps: Optional[Sequence[str]] = None


class ProjectUpdateInput(GraphQLBaseModel):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    allow_public_comments: Optional[bool] = None
    visibility: Optional[ProjectVisibility] = None


class ProjectUpdateRoleInput(GraphQLBaseModel):
    user_id: str
    project_id: str
    role: Optional[str]
