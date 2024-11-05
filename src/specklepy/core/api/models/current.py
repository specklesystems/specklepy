from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

from specklepy.core.api.enums import ProjectVisibility
from specklepy.core.api.models.deprecated import Streams

T = TypeVar("T")


class User(BaseModel):
    id: str
    email: Optional[str] = None
    name: str
    bio: Optional[str] = None
    company: Optional[str] = None
    avatar: Optional[str] = None
    verified: Optional[bool] = None
    role: Optional[str] = None
    streams: Optional["Streams"] = None

    def __repr__(self):
        return (
            f"User( id: {self.id}, name: {self.name}, email: {self.email}, company:"
            f" {self.company} )"
        )

    def __str__(self) -> str:
        return self.__repr__()


class ResourceCollection(BaseModel, Generic[T]):
    totalCount: int
    items: List[T]
    cursor: Optional[str] = None


class ServerMigration(BaseModel):
    movedFrom: Optional[str]
    movedTo: Optional[str]


class AuthStrategy(BaseModel):
    color: Optional[str]
    icon: str
    id: str
    name: str
    url: str


class ServerConfiguration(BaseModel):
    blobSizeLimitBytes: int
    objectMultipartUploadSizeLimitBytes: int
    objectSizeLimitBytes: int


# Keeping this one all Optionals at the minute, because its used both as a deserialization model for GQL and Account Management
class ServerInfo(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    url: Optional[str] = None
    adminContact: Optional[str] = None
    description: Optional[str] = None
    canonicalUrl: Optional[str] = None
    roles: Optional[List[dict]] = None
    scopes: Optional[List[dict]] = None
    authStrategies: Optional[List[dict]] = None
    version: Optional[str] = None
    frontend2: Optional[bool] = None
    migration: Optional[ServerMigration] = None

    # TODO separate gql model from account management model


class LimitedUser(BaseModel):
    """Limited user type, for showing public info about a user to another user."""

    id: str
    name: str
    bio: Optional[str]
    company: Optional[str]
    avatar: Optional[str]
    verified: Optional[bool]
    role: Optional[str]


class PendingStreamCollaborator(BaseModel):
    id: str
    inviteId: str
    streamId: Optional[str] = None
    projectId: str
    streamName: Optional[str] = None
    projectName: str
    title: str
    role: str
    invitedBy: LimitedUser
    user: Optional[LimitedUser] = None
    token: Optional[str]

    def __repr__(self):
        return (
            f"PendingStreamCollaborator( inviteId: {self.inviteId}, streamId:"
            f" {self.streamId}, role: {self.role}, title: {self.title}, invitedBy:"
            f" {self.user.name if self.user else None})"
        )

    def __str__(self) -> str:
        return self.__repr__()


class ProjectCollaborator(BaseModel):
    id: str
    role: str
    user: LimitedUser


class Version(BaseModel):
    authorUser: Optional[LimitedUser]
    createdAt: datetime
    id: str
    message: Optional[str]
    previewUrl: str
    referencedObject: str
    sourceApplication: Optional[str]


class Model(BaseModel):
    author: LimitedUser
    createdAt: datetime
    description: Optional[str]
    displayName: str
    id: str
    name: str
    previewUrl: Optional[str]
    updatedAt: datetime


class ModelWithVersions(Model):
    versions: ResourceCollection[Version]


class Project(BaseModel):
    allowPublicComments: bool
    createdAt: datetime
    description: Optional[str]
    id: str
    name: str
    role: Optional[str]
    sourceApps: List[str]
    updatedAt: datetime
    visibility: ProjectVisibility
    workspaceId: Optional[str]


class ProjectWithModels(Project):
    models: ResourceCollection[Model]


class ProjectWithTeam(Project):
    invitedTeam: List[PendingStreamCollaborator]
    team: List[ProjectCollaborator]


class ProjectCommentCollection(ResourceCollection[T], Generic[T]):
    totalArchivedCount: int


class UserSearchResultCollection(BaseModel):
    items: List[LimitedUser]
    cursor: Optional[str] = None
