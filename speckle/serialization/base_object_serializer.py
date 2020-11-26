import json
import hashlib

from typing import Tuple
from speckle.objects.base import Base


def hash_dict(obj: dict) -> str:
    return hashlib.sha224(json.dumps(obj).encode()).hexdigest()[:32]


class BaseObjectSerializer:
    detach_lineage: list = []
    closure_table: dict = {}
    traversed_objects: dict = {}
    in_iterable: bool = False

    def __init__(self) -> None:
        pass

    def to_json(self, obj: Base):
        raise NotImplementedError

    def traverse_base(self, base: Base) -> Tuple[str, dict]:
        if not self.detach_lineage:
            self.detach_lineage.append(True)
        object_dict = {"id": ""}
        obj, props = base, base.get_member_names()
        while props:
            prop = props.pop(0)
            value = obj[prop]

            # skip nulls or props marked to be ignored with "__"
            if not value or prop.startswith("__"):
                continue

            # handle base objects
            if isinstance(value, Base):
                if prop.startswith("@"):
                    self.detach_lineage.append(True)
                    ref_hash, _ = self.traverse_base(value)
                    object_dict[prop] = {
                        "reference_id": ref_hash,
                        "speckle_type": "reference",
                    }

                    if (
                        ref_hash in self.closure_table
                        and self.closure_table[ref_hash] < len(self.detach_lineage) + 1
                    ):
                        pass
                    else:
                        self.closure_table[ref_hash] = len(self.detach_lineage) + 1
                else:
                    self.detach_lineage.append(False)
                    _, child_obj = self.traverse_base(value)
                    object_dict[prop] = child_obj
                continue

            # TODO: handle iterables (lists and dictionaries)
            if isinstance(value, (list, dict)):
                self.in_iterable = True

                self.in_iterable = False

            # TODO: primitive case, unknown object case
            # all other cases
            else:
                object_dict[prop] = value

        hash = hash_dict(object_dict)
        object_dict["id"] = hash

        # write detached or root objects to transports
        if self.detach_lineage[-1]:
            self.traversed_objects[hash] = object_dict

        if self.detach_lineage and not self.in_iterable:
            self.detach_lineage.pop()

        return hash, object_dict
