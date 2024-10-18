from typing import Optional, Sequence
from pydantic import BaseModel


class UpdateVersionInput(BaseModel):
    versionId: str
    message: Optional[str]


class MoveVersionsInput(BaseModel):
    targetModelName: str
    versionIds: Sequence[str]


class DeleteVersionsInput(BaseModel):
    versionIds: Sequence[str]


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
