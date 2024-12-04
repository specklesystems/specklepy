from abc import ABC, abstractmethod
from typing import Optional

from specklepy.objects.base import Base


class ISpeckleObject(ABC):
    @abstractmethod
    def __init__(
        self,
        speckle_type: str,
        id: Optional[str] = None,
        applicationId: Optional[str] = None,
    ):

        self.speckle_type = speckle_type
        self.id = id or None
        self.applicationId = applicationId or None
