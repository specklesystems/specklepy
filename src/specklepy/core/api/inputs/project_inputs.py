from typing import Sequence

from specklepy.core.api.enums import ProjectVisibility
from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel


class ProjectCreateInput(GraphQLBaseModel):
    name: str | None
    description: str | None
    visibility: ProjectVisibility | None


class WorkspaceProjectCreateInput(GraphQLBaseModel):
    name: str | None
    description: str | None
    visibility: ProjectVisibility | None
    workspaceId: str


class ProjectInviteCreateInput(GraphQLBaseModel):
    email: str | None
    role: str | None
    server_role: str | None
    userId: str | None


class ProjectInviteUseInput(GraphQLBaseModel):
    accept: bool
    project_id: str
    token: str


class ProjectModelsFilter(GraphQLBaseModel):
    contributors: Sequence[str] | None = None
    exclude_ids: Sequence[str] | None = None
    ids: Sequence[str] | None = None
    only_with_versions: bool | None = None
    search: str | None = None
    source_apps: Sequence[str] | None = None


class ProjectUpdateInput(GraphQLBaseModel):
    id: str
    name: str | None = None
    description: str | None = None
    allow_public_comments: bool | None = None
    visibility: ProjectVisibility | None = None


class ProjectUpdateRoleInput(GraphQLBaseModel):
    user_id: str
    project_id: str
    role: str | None


class WorksaceProjectsFilter(GraphQLBaseModel):
    search: str | None
    """Filter out projects by name"""
    with_project_role_only: bool | None
    """
    Only return workspace projects that the active user has an explicit project role in
    """
