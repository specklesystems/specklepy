import contextlib
from enum import Enum
from inspect import isclass
from typing import (
    Any,
    ClassVar,
    Dict,
    ForwardRef,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    get_type_hints,
)
from warnings import warn

from stringcase import pascalcase

from specklepy.logging.exceptions import SpeckleException, SpeckleInvalidUnitException
from specklepy.objects.units import Units
from specklepy.transports.memory import MemoryTransport

PRIMITIVES = (int, float, str, bool)

# to remove from dir() when calling get_member_names()
REMOVE_FROM_DIR = {
    "Config",
    "_Base__dict_helper",
    "__annotations__",
    "__class__",
    "__delattr__",
    "__dict__",
    "__dir__",
    "__doc__",
    "__eq__",
    "__format__",
    "__ge__",
    "__getattribute__",
    "__getitem__",
    "__gt__",
    "__hash__",
    "__init__",
    "__init_subclass__",
    "__le__",
    "__lt__",
    "__module__",
    "__ne__",
    "__new__",
    "__reduce__",
    "__reduce_ex__",
    "__repr__",
    "__setattr__",
    "__setitem__",
    "__sizeof__",
    "__str__",
    "__subclasshook__",
    "__weakref__",
    "_chunk_size_default",
    "_chunkable",
    "_count_descendants",
    "_attr_types",
    "_detachable",
    "_handle_object_count",
    "_type_check",
    "_type_registry",
    "_units",
    "add_chunkable_attrs",
    "add_detachable_attrs",
    "get_children_count",
    "get_dynamic_member_names",
    "get_id",
    "get_member_names",
    "get_registered_type",
    "get_typed_member_names",
    "to_dict",
    "update_forward_refs",
    "validate_prop_name",
    "from_list",
    "to_list",
}


class _RegisteringBase:
    """
    Private Base model for Speckle types.

    This is an implementation detail, please do not use this outside this module.

    This class provides automatic registration of `speckle_type` into a global,
    (class level) registry for each subclassing type.
    The type registry is a base for accurate type based (de)serialization.
    """

    speckle_type: ClassVar[str]
    _speckle_type_override: ClassVar[Optional[str]] = None
    _speckle_namespace: ClassVar[Optional[str]] = None
    _type_registry: ClassVar[Dict[str, Type["Base"]]] = {}
    _attr_types: ClassVar[Dict[str, Type]] = {}
    # dict of chunkable props and their max chunk size
    _chunkable: Dict[str, int] = {}
    _chunk_size_default: int = 1000
    _detachable: Set[str] = set()  # list of defined detachable props
    _serialize_ignore: Set[str] = set()

    @classmethod
    def get_registered_type(cls, speckle_type: str) -> Optional[Type["Base"]]:
        """Get the registered type from the protected mapping via the `speckle_type`"""
        for full_name in reversed(speckle_type.split(":")):
            maybe_type = cls._type_registry.get(full_name, None)
            if maybe_type:
                return maybe_type
        return None

    @classmethod
    def _determine_speckle_type(cls) -> str:
        """
        This method brings the speckle_type construction in par with peckle-sharp/Core.

        The implementation differs, because in Core the basis of the speckle_type if
        type.FullName, which includes the dotnet namespace name too.
        Copying that behavior is hard in python, where the concept of namespaces
        means something entirely different.

        So we enabled a speckle_type override mechanism, that enables
        """
        base_name = "Base"
        if cls.__name__ == base_name:
            return base_name

        bases = [
            b._full_name()
            for b in reversed(cls.mro())
            if issubclass(b, Base) and b.__name__ != base_name
        ]
        return ":".join(bases)

    @classmethod
    def _full_name(cls) -> str:
        base_name = "Base"
        if cls.__name__ == base_name:
            return base_name

        if cls._speckle_type_override:
            return cls._speckle_type_override

        # convert the module names to PascalCase to match c# namespace naming convention
        # also drop specklepy from the beginning
        namespace = ".".join(
            pascalcase(m)
            for m in filter(lambda name: name != "specklepy", cls.__module__.split("."))
        )
        return f"{namespace}.{cls.__name__}"

    def __init_subclass__(
        cls,
        speckle_type: Optional[str] = None,
        chunkable: Optional[Dict[str, int]] = None,
        detachable: Optional[Set[str]] = None,
        serialize_ignore: Optional[Set[str]] = None,
        **kwargs: Dict[str, Any],
    ):
        """
        Hook into subclass type creation.

        This is provides a mechanism to hook into the event of the subclass type object
        initialization. This is reused to register each subclassing type into a class
        level dictionary.
        """
        cls._speckle_type_override = speckle_type
        cls.speckle_type = cls._determine_speckle_type()
        if cls._full_name() in cls._type_registry:
            raise ValueError(
                f"The speckle_type: {speckle_type} is already registered for type: "
                f"{cls._type_registry[cls._full_name()].__name__}. "
                "Please choose a different type name."
            )
        cls._type_registry[cls._full_name()] = cls  # type: ignore
        try:
            cls._attr_types = get_type_hints(cls)
        except Exception:
            cls._attr_types = getattr(cls, "__annotations__", {})
        if chunkable:
            chunkable = {k: v for k, v in chunkable.items() if isinstance(v, int)}
            cls._chunkable = dict(cls._chunkable, **chunkable)
        if detachable:
            cls._detachable = cls._detachable.union(detachable)
        if serialize_ignore:
            cls._serialize_ignore = cls._serialize_ignore.union(serialize_ignore)
        # we know, that the super here is object, that takes no args on init subclass
        return super().__init_subclass__()


# T = TypeVar("T")

# how i wish the code below would be correct, but we're also parsing into floats
# and converting into strings if the original type is string, but the value isn't
# def _validate_type(t: type, value: T) -> Tuple[bool, T]:


def _validate_type(t: Optional[type], value: Any) -> Tuple[bool, Any]:
    # this should be reworked. Its only ok to return null for Optionals...
    # if t is None and value is None:
    if value is None:
        return True, value

    # after fixing the None t above, this should be
    # if t is Any:
    # if t is None:

    if t is None or t is Any:
        return True, value

    if isclass(t) and issubclass(t, Enum):
        if isinstance(value, t):
            return True, value
        if value in t._value2member_map_:
            return True, t(value)

    if getattr(t, "__module__", None) == "typing":
        if isinstance(t, ForwardRef):
            return True, value

        origin = getattr(t, "__origin__")
        # below is what in nicer for >= py38
        # origin = get_origin(t)

        # recursive validation for Unions on both types preferring the fist type
        if origin is Union:
            # below is what in nicer for >= py38
            # t_1, t_2 = get_args(t)
            args = t.__args__  # type: ignore
            for arg_t in args:
                t_success, t_value = _validate_type(arg_t, value)
                if t_success:
                    return True, t_value
            return False, value
        if origin is dict:
            if not isinstance(value, dict):
                return False, value
            if value == {}:
                return True, value
            if not getattr(t, "__args__", None):
                return True, value
            t_key, t_value = t.__args__  # type: ignore

            if (
                getattr(t_key, "__name__", None),
                getattr(t_value, "__name__", None),
            ) == ("KT", "VT"):
                return True, value
            # we're only checking the first item, but the for loop and return after
            # evaluating the first item is the fastest way
            for dict_key, dict_value in value.items():
                valid_key, _ = _validate_type(t_key, dict_key)
                valid_value, _ = _validate_type(t_value, dict_value)

                if valid_key and valid_value:
                    return True, value
                return False, value

        if origin is list:
            if not isinstance(value, list):
                return False, value
            if value == []:
                return True, value
            if not hasattr(t, "__args__"):
                return True, value
            t_items = t.__args__[0]  # type: ignore
            if getattr(t_items, "__name__", None) == "T":
                return True, value
            first_item_valid, _ = _validate_type(t_items, value[0])
            if first_item_valid:
                return True, value
            return False, value

        if origin is tuple:
            if not isinstance(value, tuple):
                return False, value
            if not hasattr(t, "__args__"):
                return True, value
            args = t.__args__  # type: ignore
            if args == tuple():
                return True, value
            # we're not checking for empty tuple, cause tuple lengths must match
            if len(args) != len(value):
                return False, value
            values = []
            for t_item, v_item in zip(args, value):
                item_valid, item_value = _validate_type(t_item, v_item)
                if not item_valid:
                    return False, value
                values.append(item_value)
            return True, tuple(values)

        if origin is set:
            if not isinstance(value, set):
                return False, value
            if not hasattr(t, "__args__"):
                return True, value
            t_items = t.__args__[0]  # type: ignore
            first_item_valid, _ = _validate_type(t_items, next(iter(value)))
            if first_item_valid:
                return True, value
            return False, value

    if isinstance(value, t):
        return True, value

    with contextlib.suppress(ValueError, TypeError):
        if t is float and value is not None:
            return True, float(value)
        # TODO: dafuq, i had to add this not list check
        # but it would also fail for objects and other complex values
        if t is str and value and not isinstance(value, list):
            return True, str(value)

    return False, value


class Base(_RegisteringBase):
    id: Union[str, None] = None
    totalChildrenCount: Union[int, None] = None
    applicationId: Union[str, None] = None
    _units: Union[None, str] = None

    def __init__(self, **kwargs) -> None:
        super().__init__()
        for k, v in kwargs.items():
            self.__setattr__(k, v)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id: {self.id}, "
            f"speckle_type: {self.speckle_type}, "
            f"totalChildrenCount: {self.totalChildrenCount})"
        )

    def __str__(self) -> str:
        return self.__repr__()

    @classmethod
    def of_type(cls, speckle_type: str, **kwargs) -> "Base":
        """
        Get a plain Base object with a specified speckle_type.

        The speckle_type is protected and cannot be overwritten on a class instance.
        This is to prevent problems with receiving in other platforms or connectors.
        However, if you really need a base with a different type, here is a helper
        to do that for you.

        This is used in the deserialisation of unknown types so their speckle_type
        can be preserved.
        """
        b = cls(**kwargs)
        b.__dict__.update(speckle_type=speckle_type)
        return b

    def __setitem__(self, name: str, value: Any) -> None:
        self.validate_prop_name(name)
        self.__dict__[name] = value

    def __getitem__(self, name: str) -> Any:
        return self.__dict__[name]

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Type checking, guard attribute, and property set mechanism.

        The `speckle_type` is a protected class attribute it must not be overridden.

        This also performs a type check if the attribute is type hinted.
        """
        if name == "speckle_type":
            # not sure if we should raise an exception here??
            # raise SpeckleException(
            #     "Cannot override the `speckle_type`. This is set manually by the class or on deserialisation"
            # )
            return
        # if value is not None:
        value = self._type_check(name, value)
        attr = getattr(self.__class__, name, None)
        if isinstance(attr, property):
            try:
                attr.__set__(self, value)
            except AttributeError:
                return  # the prop probably doesn't have a setter
        super().__setattr__(name, value)

    @classmethod
    def update_forward_refs(cls) -> None:
        """
        Attempts to populate the internal defined types dict for type checking
        sometime after defining the class.
        This is already done when defining the class, but can be called
        again if references to undefined types were
        included.

        See `objects.geometry` for an example of how this is used with
        the Brep class definitions.
        """
        try:
            cls._attr_types = get_type_hints(cls)
        except Exception as e:
            warn(f"Could not update forward refs for class {cls.__name__}: {e}")

    @classmethod
    def validate_prop_name(cls, name: str) -> None:
        """Validator for dynamic attribute names."""
        if name in {"", "@"}:
            raise ValueError("Invalid Name: Base member names cannot be empty strings")
        if name.startswith("@@"):
            raise ValueError(
                "Invalid Name: Base member names cannot start with more than one '@'",
            )
        if "." in name or "/" in name:
            raise ValueError(
                "Invalid Name: Base member names cannot contain characters '.' or '/'",
            )

    def _type_check(self, name: str, value: Any) -> Any:
        """
        Lightweight type checking of values before setting them

        NOTE: Does not check subscripted types within generics as the performance hit
        of checking each item within a given collection isn't worth it.
        Eg if you have a type Dict[str, float],
        we will only check if the value you're trying to set is a dict.
        """
        types = getattr(self, "_attr_types", {})
        t = types.get(name, None)

        valid, checked_value = _validate_type(t, value)

        if valid:
            return checked_value

        raise SpeckleException(
            f"Cannot set '{self.__class__.__name__}.{name}':"
            f"it expects type '{str(t)}',"
            f"but received type '{type(value).__name__}'"
        )

    def add_chunkable_attrs(self, **kwargs: int) -> None:
        """
        Mark defined attributes as chunkable for serialisation

        Arguments:
            kwargs {int} -- the name of the attribute as the keyword
            and the chunk size as the arg
        """
        chunkable = {k: v for k, v in kwargs.items() if isinstance(v, int)}
        self._chunkable = dict(self._chunkable, **chunkable)

    def add_detachable_attrs(self, names: Set[str]) -> None:
        """
        Mark defined attributes as detachable for serialisation

        Arguments:
            names {Set[str]} -- the names of the attributes to detach as a set of string
        """
        self._detachable = self._detachable.union(names)

    @property
    def units(self) -> Union[str, None]:
        return self._units

    @units.setter
    def units(self, value: Union[str, Units, None]):
        """While this property accepts any string value, geometry expects units to be specific strings (see Units enum)"""
        if isinstance(value, str) or value is None:
            self._units = value
        elif isinstance(value, Units):
            self._units = value.value
        else:
            raise SpeckleInvalidUnitException(
                f"Unknown type {type(value)} received for units"
            )

    def get_member_names(self) -> List[str]:
        """Get all of the property names on this object, dynamic or not"""
        attr_dir = list(set(dir(self)) - REMOVE_FROM_DIR)
        return [
            name
            for name in attr_dir
            if not name.startswith("_") and not callable(getattr(self, name))
        ]

    def get_serializable_attributes(self) -> List[str]:
        """Get the attributes that should be serialized"""
        return sorted(list(set(self.get_member_names()) - self._serialize_ignore))

    def get_typed_member_names(self) -> List[str]:
        """Get all of the names of the defined (typed) properties of this object"""
        return list(self._attr_types.keys())

    def get_dynamic_member_names(self) -> List[str]:
        """Get all of the names of the dynamic properties of this object"""
        return list(set(self.__dict__.keys()) - set(self._attr_types.keys()))

    def get_children_count(self) -> int:
        """Get the total count of children Base objects"""
        parsed = []
        return 1 + self._count_descendants(self, parsed)

    def get_id(self, decompose: bool = False) -> str:
        """
        Gets the id (a unique hash) of this object.
        ⚠️ This method fully serializes the object which,
        in the case of large objects (with many sub-objects), has a tangible cost.
        Avoid using it!

        Note: the hash of a decomposed object differs from that of a
        non-decomposed object

        Arguments:
            decompose {bool} -- if True, will decompose the object in
            the process of hashing it

        Returns:
            str -- the hash (id) of the fully serialized object
        """
        from specklepy.serialization.base_object_serializer import BaseObjectSerializer

        serializer = BaseObjectSerializer()
        if decompose:
            serializer.write_transports = [MemoryTransport()]
        return serializer.traverse_base(self)[0]

    def _count_descendants(self, base: "Base", parsed: List) -> int:
        if base in parsed:
            return 0
        parsed.append(base)

        return sum(
            self._handle_object_count(value, parsed)
            for name, value in base.get_member_names()
            if not name.startswith("@")
        )

    def _handle_object_count(self, obj: Any, parsed: List) -> int:
        # pylint: disable=isinstance-second-argument-not-valid-type
        count = 0
        if obj is None:
            return count
        if isinstance(obj, "Base"):
            count += 1
            count += self._count_descendants(obj, parsed)
            return count
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, "Base"):
                    count += 1
                    count += self._count_descendants(item, parsed)
                else:
                    count += self._handle_object_count(item, parsed)
        elif isinstance(obj, dict):
            for _, value in obj.items():
                if isinstance(value, "Base"):
                    count += 1
                    count += self._count_descendants(value, parsed)
                else:
                    count += self._handle_object_count(value, parsed)
        return count


Base.update_forward_refs()


class DataChunk(Base, speckle_type="Speckle.Core.Models.DataChunk"):
    data: Union[List[Any], None] = None

    def __init__(self) -> None:
        super().__init__()
        self.data = []
