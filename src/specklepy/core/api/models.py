from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Collaborator(BaseModel):
    id: Optional[str]
    name: Optional[str]
    role: Optional[str]
    avatar: Optional[str]


class Commit(BaseModel):
    id: Optional[str]
    message: Optional[str]
    authorName: Optional[str]
    authorId: Optional[str]
    authorAvatar: Optional[str]
    branchName: Optional[str]
    createdAt: Optional[datetime]
    sourceApplication: Optional[str]
    referencedObject: Optional[str]
    totalChildrenCount: Optional[int]
    parents: Optional[List[str]]

    def __repr__(self) -> str:
        return (
            f"Commit( id: {self.id}, message: {self.message}, referencedObject:"
            f" {self.referencedObject}, authorName: {self.authorName}, branchName:"
            f" {self.branchName}, createdAt: {self.createdAt} )"
        )

    def __str__(self) -> str:
        return self.__repr__()


class Commits(BaseModel):
    totalCount: Optional[int]
    cursor: Optional[datetime]
    items: List[Commit] = []


class Object(BaseModel):
    id: Optional[str]
    speckleType: Optional[str]
    applicationId: Optional[str]
    totalChildrenCount: Optional[int]
    createdAt: Optional[datetime]


class Branch(BaseModel):
    id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    commits: Optional[Commits]


class Branches(BaseModel):
    totalCount: Optional[int]
    cursor: Optional[datetime]
    items: List[Branch] = []


class Stream(BaseModel):
    id: Optional[str] = None
    name: Optional[str]
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
    totalCount: Optional[int]
    cursor: Optional[datetime]
    items: List[Stream] = []


class User(BaseModel):
    id: Optional[str]
    email: Optional[str]
    name: Optional[str]
    bio: Optional[str]
    company: Optional[str]
    avatar: Optional[str]
    verified: Optional[bool]
    role: Optional[str]
    streams: Optional[Streams]

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
    name: Optional[str]
    bio: Optional[str]
    company: Optional[str]
    avatar: Optional[str]
    verified: Optional[bool]
    role: Optional[str]


class PendingStreamCollaborator(BaseModel):
    id: Optional[str]
    inviteId: Optional[str]
    streamId: Optional[str]
    streamName: Optional[str]
    title: Optional[str]
    role: Optional[str]
    invitedBy: Optional[User]
    user: Optional[User]
    token: Optional[str]

    def __repr__(self):
        return (
            f"PendingStreamCollaborator( inviteId: {self.inviteId}, streamId:"
            f" {self.streamId}, role: {self.role}, title: {self.title}, invitedBy:"
            f" {self.user.name if self.user else None})"
        )

    def __str__(self) -> str:
        return self.__repr__()


class Activity(BaseModel):
    actionType: Optional[str]
    info: Optional[dict]
    userId: Optional[str]
    streamId: Optional[str]
    resourceId: Optional[str]
    resourceType: Optional[str]
    message: Optional[str]
    time: Optional[datetime]

    def __repr__(self) -> str:
        return (
            f"Activity( streamId: {self.streamId}, actionType: {self.actionType},"
            f" message: {self.message}, userId: {self.userId} )"
        )

    def __str__(self) -> str:
        return self.__repr__()


class ActivityCollection(BaseModel):
    totalCount: Optional[int]
    items: Optional[List[Activity]]
    cursor: Optional[datetime]

    def __repr__(self) -> str:
        return (
            f"ActivityCollection( totalCount: {self.totalCount}, items:"
            f" {len(self.items) if self.items else 0}, cursor:"
            f" {self.cursor.isoformat() if self.cursor else None} )"
        )

    def __str__(self) -> str:
        return self.__repr__()


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
