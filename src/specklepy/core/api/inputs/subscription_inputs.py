from typing import Optional
from pydantic import BaseModel


class ViewerUpdateTrackingTarget(BaseModel):
    projectId: str
    resourceIdString: str
    loadedVersionsOnly: Optional[bool] = None
