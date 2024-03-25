from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Collaborator(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    avatar: Optional[str] = None


class Commit(BaseModel):
    id: Optional[str] = None
    message: Optional[str] = None
    authorName: Optional[str] = None
    authorId: Optional[str] = None
    authorAvatar: Optional[str] = None
    branchName: Optional[str] = None
    createdAt: Optional[datetime] = None
    sourceApplication: Optional[str] = None
    referencedObject: Optional[str] = None
    totalChildrenCount: Optional[int] = None
    parents: Optional[List[str]] = None

    def __repr__(self) -> str:
        return (
            f"Commit( id: {self.id}, message: {self.message}, referencedObject:"
            f" {self.referencedObject}, authorName: {self.authorName}, branchName:"
            f" {self.branchName}, createdAt: {self.createdAt} )"
        )

    def __str__(self) -> str:
        return self.__repr__()


class Commits(BaseModel):
    totalCount: Optional[int] = None
    cursor: Optional[datetime] = None
    items: List[Commit] = []


class Object(BaseModel):
    id: Optional[str] = None
    speckleType: Optional[str] = None
    applicationId: Optional[str] = None
    totalChildrenCount: Optional[int] = None
    createdAt: Optional[datetime] = None


class Branch(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    commits: Optional[Commits] = None


class Branches(BaseModel):
    totalCount: Optional[int] = None
    cursor: Optional[datetime] = None
    items: List[Branch] = []


class Stream(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    isPublic: Optional[bool] = None
    description: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    collaborators: List[Collaborator] = Field(default_factory=list)
    branches: Optional[Branches] = None
    commit: Optional[Commit] = None
    object: Optional[Object] = None
    commentCount: Optional[int] = None
    favoritedDate: Optional[datetime] = None
    favoritesCount: Optional[int] = None

    def __repr__(self):
        return (
            f"Stream( id: {self.id}, name: {self.name}, description:"
            f" {self.description}, isPublic: {self.isPublic})"
        )

    def __str__(self) -> str:
        return self.__repr__()


class Streams(BaseModel):
    totalCount: Optional[int] = None
    cursor: Optional[datetime] = None
    items: List[Stream] = []


class User(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    avatar: Optional[str] = None
    verified: Optional[bool] = None
    role: Optional[str] = None
    streams: Optional[Streams] = None

    def __repr__(self):
        return (
            f"User( id: {self.id}, name: {self.name}, email: {self.email}, company:"
            f" {self.company} )"
        )

    def __str__(self) -> str:
        return self.__repr__()


class LimitedUser(BaseModel):
    """Limited user type, for showing public info about a user to another user."""

    id: str
    name: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    avatar: Optional[str] = None
    verified: Optional[bool] = None
    role: Optional[str] = None


class PendingStreamCollaborator(BaseModel):
    id: Optional[str] = None
    inviteId: Optional[str] = None
    streamId: Optional[str] = None
    streamName: Optional[str] = None
    title: Optional[str] = None
    role: Optional[str] = None
    invitedBy: Optional[User] = None
    user: Optional[User] = None
    token: Optional[str] = None

    def __repr__(self):
        return (
            f"PendingStreamCollaborator( inviteId: {self.inviteId}, streamId:"
            f" {self.streamId}, role: {self.role}, title: {self.title}, invitedBy:"
            f" {self.user.name if self.user else None})"
        )

    def __str__(self) -> str:
        return self.__repr__()


class Activity(BaseModel):
    actionType: Optional[str] = None
    info: Optional[dict] = None
    userId: Optional[str] = None
    streamId: Optional[str] = None
    resourceId: Optional[str] = None
    resourceType: Optional[str] = None
    message: Optional[str] = None
    time: Optional[datetime] = None

    def __repr__(self) -> str:
        return (
            f"Activity( streamId: {self.streamId}, actionType: {self.actionType},"
            f" message: {self.message}, userId: {self.userId} )"
        )

    def __str__(self) -> str:
        return self.__repr__()


class ActivityCollection(BaseModel):
    totalCount: Optional[int] = None
    items: Optional[List[Activity]] = None
    cursor: Optional[datetime] = None

    def __repr__(self) -> str:
        return (
            f"ActivityCollection( totalCount: {self.totalCount}, items:"
            f" {len(self.items) if self.items else 0}, cursor:"
            f" {self.cursor.isoformat() if self.cursor else None} )"
        )

    def __str__(self) -> str:
        return self.__repr__()


class ServerMigration(BaseModel):
    movedTo: Optional[str] = None
    movedFrom: Optional[str] = None


class ServerInfo(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    adminContact: Optional[str] = None
    canonicalUrl: Optional[str] = None
    roles: Optional[List[dict]] = None
    scopes: Optional[List[dict]] = None
    authStrategies: Optional[List[dict]] = None
    version: Optional[str] = None
    frontend2: Optional[bool] = None
    migration: Optional[ServerMigration] = None
