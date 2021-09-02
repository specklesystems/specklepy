import typing
from warnings import warn
from typing import get_type_hints
from typing import ClassVar, Dict, List, Optional, Any, Set, Type
from specklepy.transports.memory import MemoryTransport
from specklepy.logging.exceptions import SpeckleException
from specklepy.objects.units import get_units_from_string


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
    _type_registry: ClassVar[Dict[str, "Base"]] = {}
    _attr_types: ClassVar[Dict[str, Type]] = {}

    class Config:
        validate_assignment = True

    @classmethod
    def get_registered_type(cls, speckle_type: str) -> Optional[Type["Base"]]:
        """Get the registered type from the protected mapping via the `speckle_type`"""
        return cls._type_registry.get(speckle_type, None)

    def __init_subclass__(
        cls,
        speckle_type: str = None,
        chunkable: Dict[str, int] = None,
        detachable: Set[str] = None,
        **kwargs: Dict[str, Any],
    ):
        """
        Hook into subclass type creation.

        This is provides a mechanism to hook into the event of the subclass type object
        initialization. This is reused to register each subclassing type into a class
        level dictionary.
        """
        if speckle_type in cls._type_registry:
            raise ValueError(
                f"The speckle_type: {speckle_type} is already registered for type: "
                f"{cls._type_registry[speckle_type].__name__}. "
                f"Please choose a different type name."
            )
        cls.speckle_type = speckle_type or cls.__name__
        cls._type_registry[cls.speckle_type] = cls  # type: ignore
        try:
            cls._attr_types = get_type_hints(cls)
        except Exception:
            cls._attr_types = getattr(cls, "__annotations__", {})
        if chunkable:
            chunkable = {k: v for k, v in chunkable.items() if isinstance(v, int)}
            cls._chunkable = dict(cls._chunkable, **chunkable)
        if detachable:
            cls._detachable = cls._detachable.union(detachable)
        super().__init_subclass__(**kwargs)


class Base(_RegisteringBase):
    id: Optional[str] = None
    totalChildrenCount: Optional[int] = None
    applicationId: Optional[str] = None
    _units: str = "m"
    _chunkable: Dict[str, int] = {}  # dict of chunkable props and their max chunk size
    _chunk_size_default: int = 1000
    _detachable: Set[str] = set()  # list of defined detachable props

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
                pass  # the prop probably doesn't have a setter
        super().__setattr__(name, value)

    @classmethod
    def update_forward_refs(cls) -> None:
        """
        Attempts to populate the internal defined types dict for type checking sometime after defining the class.
        This is already done when defining the class, but can be called again if references to undefined types were
        included.

        See `objects.geometry` for an example of how this is used with the Brep class definitions
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

    def _type_check(self, name: str, value: Any):
        """
        Lightweight type checking of values before setting them

        NOTE: Does not check subscripted types within generics as the performance hit of checking
        each item within a given collection isn't worth it. Eg if you have a type Dict[str, float],
        we will only check if the value you're trying to set is a dict.
        """
        types = getattr(self, "_attr_types", {})
        t = types.get(name, None)

        if t is None:
            return value

        if t.__module__ == "typing":
            origin = getattr(t, "__origin__")
            t = t.__args__ if origin is typing.Union else origin
            if not isinstance(t, (type, tuple)):
                warn(
                    f"Unrecognised type '{t}' provided for attribute '{name}'. Type will not been validated."
                )
                return value
        if isinstance(value, t):
            return value

        # to be friendly, we'll parse ints and strs into floats, but not the other way around
        # (to avoid unexpected rounding)
        if t is float and isinstance(value, (int, str, float)):
            try:
                return float(value)
            except ValueError:
                pass
        if t is str and value is not None:
            return str(value)

        raise SpeckleException(
            f"Cannot set '{self.__class__.__name__}.{name}': it expects type '{t.__name__}', but received type '{type(value).__name__}'"
        )

    def add_chunkable_attrs(self, **kwargs: int) -> None:
        """
        Mark defined attributes as chunkable for serialisation

        Arguments:
            kwargs {int} -- the name of the attribute as the keyword and the chunk size as the arg
        """
        chunkable = {k: v for k, v in kwargs.items() if isinstance(v, int)}
        self._chunkable = dict(self._chunkable, **chunkable)

    def add_detachable_attrs(self, names: Set[str]) -> None:
        """
        Mark defined attributes as detachable for serialisation

        Arguments:
            names {Set[str]} -- the names of the attributes to detach as a set of strings
        """
        self._detachable = self._detachable.union(names)

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, value: str):
        self._units = get_units_from_string(value)

    # def to_dict(self) -> Dict[str, Any]:
    #     """Convenience method to view the whole base object as a dict"""
    #     base_dict = self.__dict__
    #     for key, value in base_dict.items():
    #         if not value or isinstance(value, PRIMITIVES):
    #             continue
    #         else:
    #             base_dict[key] = self.__dict_helper(value)
    #     return base_dict

    # def __dict_helper(self, obj: Any) -> Any:
    #     if not obj or isinstance(obj, PRIMITIVES):
    #         return obj
    #     if isinstance(obj, Base):
    #         return self.__dict_helper(obj.__dict__)
    #     if isinstance(obj, (list, set)):
    #         return [self.__dict_helper(v) for v in obj]
    #     if not isinstance(obj, dict):
    #         raise SpeckleException(
    #             message=f"Could not convert to dict due to unrecognized type: {type(obj)}"
    #         )

    #     for k, v in obj.items():
    #         if v and not isinstance(obj, PRIMITIVES):
    #             obj[k] = self.__dict_helper(v)
    #     return obj

    def get_member_names(self) -> List[str]:
        """Get all of the property names on this object, dynamic or not"""
        # attrs = set(self.__dict__.keys())
        attr_dir = list(set(dir(self)) - REMOVE_FROM_DIR)
        return [
            name
            for name in attr_dir
            if not name.startswith("_") and not callable(getattr(self, name))
        ]

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
        Gets the id (a unique hash) of this object. ⚠️ This method fully serializes the object, which in the case of large objects (with many sub-objects), has a tangible cost. Avoid using it!

        Note: the hash of a decomposed object differs from that of a non-decomposed object

        Arguments:
            decompose {bool} -- if True, will decompose the object in the process of hashing it

        Returns:
            str -- the hash (id) of the fully serialized object
        """
        from specklepy.serialization.base_object_serializer import (
            BaseObjectSerializer,
        )

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
    data: List[Any] = None

    def __init__(self) -> None:
        self.data = []
