from typing import Any, Optional, Sequence

from pydantic import BaseModel


class CommentContentInput(BaseModel):
    blobIds: Optional[Sequence[str]]
    doc: Any


class CreateCommentInput(BaseModel):
    content: CommentContentInput
    projectId: str
    resourceIdString: str
    screenshot: Optional[str]
    viewerState: Optional[Any]


class EditCommentInput(BaseModel):
    content: CommentContentInput
    commentId: str


class CreateCommentReplyInput(BaseModel):
    content: CommentContentInput
    threadId: str
