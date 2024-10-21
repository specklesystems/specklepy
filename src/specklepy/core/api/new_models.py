from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from specklepy.core.api.enums import (
    FileUploadConversionStatus,
    ProjectVisibility,
    ResourceType,
)
from specklepy.core.api.responses import ResourceCollection


class ServerMigration(BaseModel):
    movedFrom: Optional[str] = None
    movedTo: Optional[str] = None


class AuthStrategy(BaseModel):
    color: Optional[str] = None
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
    bio: Optional[str] = None
    company: Optional[str] = None
    avatar: Optional[str] = None
    verified: Optional[bool] = None
    role: Optional[str] = None


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


class ResourceIdentifier(BaseModel):
    resourceId: str
    resourceType: ResourceType


class ViewerResourceItem(BaseModel):
    modelId: Optional[str] = None
    objectId: str
    versionId: Optional[str] = None


class ViewerResourceGroup(BaseModel):
    identifier: str
    items: List[ViewerResourceItem]


class Comment(BaseModel):
    archived: bool
    author: LimitedUser
    authorId: str
    createdAt: datetime
    hasParent: bool
    id: str
    parent: Optional["Comment"] = None
    rawText: str
    replies: ResourceCollection["Comment"]
    replyAuthors: ResourceCollection[LimitedUser]
    resources: List[ResourceIdentifier]
    screenshot: Optional[str] = None
    updatedAt: datetime
    viewedAt: Optional[datetime] = None
    viewerResources: List[ViewerResourceItem]


class Version(BaseModel):
    authorUser: Optional[LimitedUser] = None
    commentThreads: List[Comment]
    createdAt: datetime
    id: str
    message: Optional[str] = None
    model: "Model"
    previewUrl: str
    referencedObject: str
    sourceApplication: Optional[str] = None


class ModelsTreeItem(BaseModel):
    children: List["ModelsTreeItem"]
    fullName: str
    hasChildren: bool
    id: str
    model: Optional["Model"] = None
    name: str
    updatedAt: datetime


class FileUpload(BaseModel):
    convertedCommitId: Optional[str] = None
    convertedLastUpdate: datetime
    convertedMessage: Optional[str] = None
    convertedStatus: FileUploadConversionStatus
    convertedVersionId: Optional[str] = None
    fileName: str
    fileSize: int
    fileType: str
    id: str
    model: Optional["Model"] = None
    modelName: str
    projectId: str
    uploadComplete: bool
    uploadDate: datetime
    userId: str


class Model(BaseModel):
    author: LimitedUser
    childrenTree: List[ModelsTreeItem]
    commentThreads: ResourceCollection[Comment]
    createdAt: datetime
    description: str
    displayName: str
    id: str
    name: str
    pendingImportedVersions: List[FileUpload]
    previewUrl: Optional[str] = None
    updatedAt: datetime
    versions: ResourceCollection[Version]
    version: Version


class Project(BaseModel):
    allowPublicComments: bool
    createdAt: datetime
    description: Optional[str] = None
    id: str
    name: str
    role: Optional[str] = None
    sourceApps: List[str]
    updatedAt: datetime
    visibility: ProjectVisibility
    workspaceId: Optional[str] = None


class ProjectWithModels(Project):
    models: ResourceCollection[Model]


class ProjectWithTeam(Project):
    invitedTeam: List[PendingStreamCollaborator]
    team: List[ProjectCollaborator]
