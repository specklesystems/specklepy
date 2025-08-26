from datetime import datetime
from typing import Generic, List, TypeVar

from specklepy.core.api.enums import ProjectVisibility
from specklepy.core.api.models.graphql_base_model import GraphQLBaseModel
from specklepy.logging.exceptions import WorkspacePermissionException

T = TypeVar("T")


class User(GraphQLBaseModel):
    id: str
    email: str | None = None
    name: str
    bio: str | None = None
    company: str | None = None
    avatar: str | None = None
    verified: bool | None = None
    role: str | None = None

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
    cursor: str | None = None


class ServerMigration(GraphQLBaseModel):
    moved_from: str | None
    moved_to: str | None


class AuthStrategy(GraphQLBaseModel):
    color: str | None
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
    name: str | None = None
    company: str | None = None
    url: str | None = None
    admin_contact: str | None = None
    description: str | None = None
    canonical_url: str | None = None
    scopes: List[dict] | None = None
    auth_strategies: List[dict] | None = None
    version: str | None = None
    migration: ServerMigration | None = None
    workspaces: ServerWorkspacesInfo | None = None
    # TODO separate gql model from account management model


class LimitedUser(GraphQLBaseModel):
    """Limited user type, for showing public info about a user to another user."""

    id: str
    name: str
    bio: str | None
    company: str | None
    avatar: str | None
    verified: bool | None
    role: str | None

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
    stream_id: str | None = None
    projectId: str
    stream_name: str | None = None
    project_name: str
    title: str
    role: str
    invited_by: LimitedUser
    user: LimitedUser | None = None
    token: str | None

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
    author_user: LimitedUser | None
    created_at: datetime
    id: str
    message: str | None
    preview_url: str
    referenced_object: str | None
    """Maybe null if workspaces version history limit has been exceeded"""
    source_application: str | None


class Model(GraphQLBaseModel):
    author: LimitedUser | None
    created_at: datetime
    description: str | None
    display_name: str
    id: str
    name: str
    preview_url: str | None
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
    description: str | None
    id: str
    name: str
    role: str | None
    source_apps: List[str]
    updated_at: datetime
    visibility: ProjectVisibility
    workspace_id: str | None


class ProjectWithModels(Project):
    models: ResourceCollection[Model]


class ProjectWithPermissions(Project):
    permissions: ProjectPermissionChecks


class ProjectWithTeam(Project):
    invited_team: List[PendingStreamCollaborator]
    team: List[ProjectCollaborator]


class ProjectCommentCollection(ResourceCollection[T], Generic[T]):
    total_archived_count: int


class UserSearchResultCollection(GraphQLBaseModel):
    items: List[LimitedUser]
    cursor: str | None = None


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


class LimitedWorkspace(GraphQLBaseModel):
    id: str
    name: str
    role: str | None
    slug: str
    logo: str | None
    description: str | None


class Workspace(LimitedWorkspace):
    created_at: datetime
    updated_at: datetime
    read_only: bool
    creation_state: WorkspaceCreationState | None
    permissions: WorkspacePermissionChecks


class FileImport(GraphQLBaseModel):
    id: str
    project_id: str
    converted_version_id: str | None
    user_id: str
    converted_status: int
    converted_message: str | None
    model_id: str | None
    updated_at: datetime


class FileUploadUrl(GraphQLBaseModel):
    url: str
    file_id: str
