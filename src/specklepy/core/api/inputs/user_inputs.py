from typing import Sequence

from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel


class UserUpdateInput(GraphQLBaseModel):
    avatar: str | None = None
    bio: str | None = None
    company: str | None = None
    name: str | None = None


class UserProjectsFilter(GraphQLBaseModel):
    search: str | None = None
    only_with_roles: Sequence[str] | None = None
    workspace_id: str | None = None
    personal_only: bool | None = None
    include_implicit_access: bool | None = None


class UserWorkspacesFilter(GraphQLBaseModel):
    search: str | None
