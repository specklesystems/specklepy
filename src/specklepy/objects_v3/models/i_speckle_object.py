# public interface ISpeckleObject
# {
#   public string? id { get; }

#   public string? applicationId { get; }

#   public string speckle_type { get; }
# }


from abc import ABCMeta

from specklepy.objects.base import Base


class ISpeckleObject(Base, speckle_type="ISpeckleObjects", metaclass=ABCMeta):
    pass
