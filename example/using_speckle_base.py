"""This is an example showcasing the usage of speckle `Base` class."""

# the speckle.objects module exposes all speckle provided classes
from devtools import debug

from specklepy.api import operations
from specklepy.objects import Base


class ExampleSub(Base):
    """
    Inheriting from `Base` is done with in the standard way by default.

    The syntax is similar to the stdlib dataclass syntax.
    No __init__ method definition is required, that is done automatically by the base
    type. Also the attributes defined this way are instance attributes despite they
    might look like class attributes.

    The speckle Base uses the pydantic BaseModel in the background, but ideally that
    is not the consumers concern.

    **Important note:** currently the way how serialization works, requires
    each attribute to have a valid default value, just like `foo` has. This includes
    default values for all primitives and complex datastructures.
    Failing to provide a default, breaks the receiving end of the transport.
    """

    foo: str = "bar"


class SpeckleSub(ExampleSub, speckle_type="custom_speckle_sub"):
    """
    Example custom type name registration.

    This is an optional feature.
    The default value of the speckle_type is generated from the name of the class, but
    optionally it may be overridden. This is useful, since the speckle_type has to be
    unique for each subclass of speckle Base.
    """

    magic: str = "trick"


if __name__ == "__main__":
    # example usage
    custom_sub = SpeckleSub(
        foo=123,
        magic="trick",
        bar="baric",
        extra=123,
    )
    # support for dynamic attributes
    custom_sub.extra_extra = "what is this?"
    debug(custom_sub)

    serialized = operations.serialize(custom_sub)
    deserialized = operations.deserialize(serialized)
    # the only difference should be between the two data is that the deserialized
    # instance id attribute is not None.
    debug(deserialized)
