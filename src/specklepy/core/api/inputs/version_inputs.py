from typing import Optional, Sequence

from pydantic import BaseModel


class UpdateVersionInput(BaseModel):
    versionId: str
    projectId: str
    message: Optional[str]


class MoveVersionsInput(BaseModel):
    targetModelName: str
    versionIds: Sequence[str]
    projectId: str


class DeleteVersionsInput(BaseModel):
    versionIds: Sequence[str]
    projectId: str


class CreateVersionInput(BaseModel):
    objectId: str
    modelId: str
    projectId: str
    message: Optional[str] = None
    sourceApplication: Optional[str] = "py"
    totalChildrenCount: Optional[int] = None
    parents: Optional[Sequence[str]] = None


class MarkReceivedVersionInput(BaseModel):
    versionId: str
    projectId: str
    sourceApplication: str
    message: Optional[str] = None
