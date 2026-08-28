from abc import ABCMeta, abstractmethod


class ISpeckleObject(metaclass=ABCMeta):
    @property
    @abstractmethod
    def id(self) -> str | None:
        pass

    @property
    @abstractmethod
    def application_id(self) -> str | None:
        pass

    @property
    @abstractmethod
    def speckle_type(self) -> str:
        pass
