import json
import hashlib

from typing import Tuple
from speckle.objects.base import Base


def hash_dict(obj: dict) -> str:
    return hashlib.sha224(json.dumps(obj).encode()).hexdigest()[0:32]


class BaseObjectSerializer:
    def __init__(self) -> None:
        pass

    def to_json(self, obj: Base):
        raise NotImplementedError

    def traverse_base(self, base: Base) -> Tuple[str, dict]:
        stack = [(base, base.get_member_names())]
        object_dict = {}
        while stack:
            obj, props = stack.pop()
            while props:
                prop = props.pop()
                value = obj[prop]
                if not value or prop.startswith("__"):
                    continue
                if isinstance(value, Base):
                    ref_hash, child_obj = self.traverse_base(value)
                    if prop.startswith(("@", "__")):
                        object_dict[prop] = {
                            "reference_id": ref_hash,
                            "speckle_type": "reference",
                        }
                    else:
                        object_dict[prop] = child_obj
                    stack.extend([(obj, props)])
                    break
                object_dict[prop] = value
        hash = hash_dict(object_dict)
        object_dict["id"] = hash

        # print(f"==== traversed base {base.name} ====")
        # print(json.dumps(object_dict, indent=2))

        return hash, object_dict
