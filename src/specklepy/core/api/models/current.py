from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from specklepy.core.api.enums import ProjectVisibility
from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel
from specklepy.logging.exceptions import WorkspacePermissionException

T = TypeVar("T")


class User(GraphQLBaseModel):
    id: str
    email: Optional[str] = None
    name: str
    bio: Optional[str] = None
    company: Optional[str] = None
    avatar: Optional[str] = None
    verified: Optional[bool] = None
    role: Optional[str] = None

    def __repr__(self):
        return (
            f"User( id: {self.id}, name: {self.name}, email: {self.email}, company:"
            f" {self.company} )"
        )

    def __str__(self) -> str:
        return self.__repr__()


class ResourceCollection(GraphQLBaseModel, Generic[T]):
    total_count: int
    items: List[T]
    cursor: Optional[str] = None


class ServerMigration(GraphQLBaseModel):
    moved_from: Optional[str]
    moved_to: Optional[str]


class AuthStrategy(GraphQLBaseModel):
    color: Optional[str]
    icon: str
    id: str
    name: str
    url: str


class ServerConfiguration(GraphQLBaseModel):
    blob_size_limit_bytes: int
    object_multipart_upload_size_limit_bytes: int
    object_size_limit_bytes: int


class ServerWorkspacesInfo(GraphQLBaseModel):
    workspaces_enabled: bool


# Keeping this one all Optionals at the minute,
#  because its used both as a deserialization model for GQL and Account Management
class ServerInfo(GraphQLBaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    url: Optional[str] = None
    admin_contact: Optional[str] = None
    description: Optional[str] = None
    canonical_url: Optional[str] = None
    scopes: Optional[List[dict]] = None
    auth_strategies: Optional[List[dict]] = None
    version: Optional[str] = None
    migration: Optional[ServerMigration] = None
    workspaces: Optional[ServerWorkspacesInfo] = None
    # TODO separate gql model from account management model


class LimitedUser(GraphQLBaseModel):
    """Limited user type, for showing public info about a user to another user."""

    id: str
    name: str
    bio: Optional[str]
    company: Optional[str]
    avatar: Optional[str]
    verified: Optional[bool]
    role: Optional[str]

    def __repr__(self):
        return (
            f"(name: {self.name}, "
            f"id: {self.id}, "
            f"bio: {self.bio}, "
            f"company: {self.company}, "
            f"verified: {self.verified}, "
            f"role: {self.role})"
        )


class PendingStreamCollaborator(GraphQLBaseModel):
    id: str
    invite_id: str
    stream_id: Optional[str] = None
    projectId: str
    stream_name: Optional[str] = None
    project_name: str
    title: str
    role: str
    invited_by: LimitedUser
    user: Optional[LimitedUser] = None
    token: Optional[str]

    def __repr__(self):
        return (
            f"PendingStreamCollaborator( inviteId: {self.invite_id}, streamId:"
            f" {self.stream_id}, role: {self.role}, title: {self.title}, invitedBy:"
            f" {self.user.name if self.user else None})"
        )

    def __str__(self) -> str:
        return self.__repr__()


class ProjectCollaborator(GraphQLBaseModel):
    id: str
    role: str
    user: LimitedUser


class Version(GraphQLBaseModel):
    author_user: Optional[LimitedUser]
    created_at: datetime
    id: str
    message: Optional[str]
    preview_url: str
    referenced_object: Optional[str]
    """Maybe null if workspaces version history limit has been exceeded"""
    source_application: Optional[str]


class Model(GraphQLBaseModel):
    author: Optional[LimitedUser]
    created_at: datetime
    description: Optional[str]
    display_name: str
    id: str
    name: str
    preview_url: Optional[str]
    updated_at: datetime


class ModelWithVersions(Model):
    versions: ResourceCollection[Version]


class ProjectPermissionChecks(GraphQLBaseModel):
    can_create_model: "PermissionCheckResult"
    can_delete: "PermissionCheckResult"
    can_load: "PermissionCheckResult"
    can_publish: "PermissionCheckResult"


class Project(GraphQLBaseModel):
    allow_public_comments: bool
    created_at: datetime
    description: Optional[str]
    id: str
    name: str
    role: Optional[str]
    source_apps: List[str]
    updated_at: datetime
    visibility: ProjectVisibility
    workspace_id: Optional[str]


class ProjectWithModels(Project):
    models: ResourceCollection[Model]


class ProjectWithTeam(Project):
    invited_team: List[PendingStreamCollaborator]
    team: List[ProjectCollaborator]


class ProjectCommentCollection(ResourceCollection[T], Generic[T]):
    total_archived_count: int


class UserSearchResultCollection(GraphQLBaseModel):
    items: List[LimitedUser]
    cursor: Optional[str] = None


class PermissionCheckResult(GraphQLBaseModel):
    authorized: bool
    code: str
    message: str

    def ensure_authorised(self) -> None:
        """Raises WorkspacePermissionException if not authorized"""
        if not self.authorized:
            raise WorkspacePermissionException(self.message)


class WorkspacePermissionChecks(GraphQLBaseModel):
    can_create_project: PermissionCheckResult


class WorkspaceCreationState(GraphQLBaseModel):
    completed: bool


class Workspace(GraphQLBaseModel):
    id: str
    name: str
    role: Optional[str]
    slug: str
    logo: Optional[str]
    created_at: datetime
    updated_at: datetime
    read_only: bool
    description: Optional[str]
    creation_state: Optional[WorkspaceCreationState]
    permissions: WorkspacePermissionChecks
