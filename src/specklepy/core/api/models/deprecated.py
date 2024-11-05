from datetime import datetime
from typing import List, Optional

from deprecated import deprecated
from pydantic import BaseModel, Field

FE1_DEPRECATION_REASON = "Stream/Branch/Commit API is now deprecated, Use the new Project/Model/Version API functions in Client}"
FE1_DEPRECATION_VERSION = "2.20"


@deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
class Collaborator(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    avatar: Optional[str] = None


@deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
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


@deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
class Commits(BaseModel):
    totalCount: Optional[int] = None
    cursor: Optional[datetime] = None
    items: List[Commit] = []


@deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
class Object(BaseModel):
    id: Optional[str] = None
    speckleType: Optional[str] = None
    applicationId: Optional[str] = None
    totalChildrenCount: Optional[int] = None
    createdAt: Optional[datetime] = None


@deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
class Branch(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    commits: Optional[Commits] = None


@deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
class Branches(BaseModel):
    totalCount: Optional[int] = None
    cursor: Optional[datetime] = None
    items: List[Branch] = []


@deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
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


@deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
class Streams(BaseModel):
    totalCount: Optional[int] = None
    cursor: Optional[datetime] = None
    items: List[Stream] = []


@deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
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


@deprecated(reason=FE1_DEPRECATION_REASON, version=FE1_DEPRECATION_VERSION)
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
