import json
import hashlib

from typing import Tuple
from speckle.objects.base import Base


def hash_dict(obj: dict) -> str:
    return hashlib.sha224(json.dumps(obj).encode()).hexdigest()[0:32]


class BaseObjectSerializer:
    detach_lineage: list = []
    closure_table: dict = {}
    traversed_objects: dict = {}

    def __init__(self) -> None:
        pass

    def to_json(self, obj: Base):
        raise NotImplementedError

    def traverse_base(self, base: Base) -> Tuple[str, dict]:
        if not self.detach_lineage:
            self.detach_lineage.append(False)
        stack = [(base, base.get_member_names())]
        object_dict = {"id": ""}
        while stack:
            obj, props = stack.pop()
            while props:
                prop = props.pop(0)
                value = obj[prop]
                if not value or prop.startswith("__"):
                    continue
                if isinstance(value, Base):
                    if prop.startswith(("@", "__")):
                        self.detach_lineage.append(True)
                        ref_hash, _ = self.traverse_base(value)
                        object_dict[prop] = {
                            "reference_id": ref_hash,
                            "speckle_type": "reference",
                        }
                        self.closure_table[ref_hash] = len(self.detach_lineage) + 1
                    else:
                        self.detach_lineage.append(False)
                        _, child_obj = self.traverse_base(value)
                        object_dict[prop] = child_obj
                    stack.extend([(obj, props)])
                    break
                object_dict[prop] = value
        hash = hash_dict(object_dict)
        object_dict["id"] = hash
        self.traversed_objects[hash] = object_dict

        if self.detach_lineage:
            self.detach_lineage.pop()

        return hash, object_dict
