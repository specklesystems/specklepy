from typing import Optional, Sequence

from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel


class UserUpdateInput(GraphQLBaseModel):
    avatar: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    name: Optional[str] = None


class UserProjectsFilter(GraphQLBaseModel):
    search: Optional[str] = None
    only_with_roles: Optional[Sequence[str]] = None
    workspace_id: Optional[str] = None
    personal_only: Optional[bool] = None
    include_implicit_access: Optional[bool] = None


class UserWorkspacesFilter(GraphQLBaseModel):
    search: Optional[str]
