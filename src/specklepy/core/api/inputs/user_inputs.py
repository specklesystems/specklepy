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
    workspaceId: Optional[str] = None
    personalOnly: Optional[bool] = None


class UserWorkspacesFilter(GraphQLBaseModel):
    search: Optional[str]
