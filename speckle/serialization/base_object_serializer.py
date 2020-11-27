import json
import hashlib

from typing import Any, Dict, List, Tuple
from speckle.objects.base import Base
from speckle.logging.exceptions import SerializationException

PRIMITIVES = (int, float, str, bool)


def hash_obj(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj).encode()).hexdigest()[:32]


class BaseObjectSerializer:
    detach_lineage: List[bool] = []  # tracks depth and whether or not to detach
    family_tree: Dict = [{}]  # holds all the children in the root object
    leaf: int = 0
    traversed_objects: Dict = {}  # all bases (root and its detached children)
    closure_table: Dict = {}  # hash of each base and its children with min depth

    def __init__(self) -> None:
        pass

    def to_json(self, base: Base):
        self.detach_lineage = [True]

    def traverse_base(self, base: Base) -> Tuple[str, dict]:
        if not self.detach_lineage:
            self.detach_lineage.append(True)
        object_dict = {"id": ""}
        children = []
        obj, props = base, base.get_member_names()

        while props:
            prop = props.pop(0)
            value = obj[prop]

            # skip nulls or props marked to be ignored with "__"
            if not value or prop.startswith("__"):
                continue

            # handle primitives (ints, floats, strings, and bools)
            elif isinstance(value, PRIMITIVES):
                object_dict[prop] = value

            # handle base objects
            elif isinstance(value, Base):
                if prop.startswith("@"):
                    self.detach_lineage.append(True)

                    ref_hash, child_obj = self.traverse_base(value)
                    children.append(ref_hash)

                    object_dict[prop] = self.detach_helper(
                        ref_hash=ref_hash, obj=child_obj
                    )

                else:
                    self.detach_lineage.append(False)

                    _, child_obj = self.traverse_base(value)
                    object_dict[prop] = child_obj

            # handle lists and dicts
            elif isinstance(value, (list, dict)):
                self.leaf += 1
                self.family_tree.append({})

                if prop.startswith("@"):
                    traversed = self.traverse_value(value, detach=True)
                    ref_hash = hash_obj(traversed)
                    object_dict[prop] = self.detach_helper(
                        ref_hash=ref_hash, obj=traversed
                    )
                    children.append(ref_hash)

                else:
                    traversed = self.traverse_value(value)
                    object_dict[prop] = traversed

                self.leaf -= 1
                for hash, depth in self.family_tree.pop().items():
                    if (
                        hash in self.family_tree[self.leaf]
                        and self.family_tree[self.leaf][hash] < depth
                    ):
                        pass
                    else:
                        self.family_tree[self.leaf][hash] = depth

            # all other cases
            elif prop.startswith("@"):
                self.detach_lineage.append(True)
                traversed = self.traverse_value(value, detach=True)
                ref_hash = hash_obj(traversed)
                object_dict[prop] = self.detach_helper(ref_hash=ref_hash, obj=traversed)
                children.append(ref_hash)

            else:
                self.detach_lineage.append(False)
                traversed = self.traverse_value(value)
                object_dict[prop] = traversed

        hash = hash_obj(object_dict)
        object_dict["id"] = hash

        # write detached or root objects to transports
        if self.detach_lineage[-1]:
            self.traversed_objects[hash] = object_dict

        if self.detach_lineage:
            self.detach_lineage.pop()

        # add closures to object and to closure table
        if children:
            lineage_length = len(self.detach_lineage)
            object_dict["__closure"] = self.closure_table[hash] = {
                hash: minDepth - lineage_length if lineage_length > 0 else minDepth
                for hash, minDepth in self.family_tree[self.leaf].items()
            }

        return hash, object_dict

    def traverse_value(self, obj: Any, detach: bool = False) -> Any:
        if isinstance(obj, PRIMITIVES):
            return obj

        elif isinstance(obj, (list, set)):
            return [self.traverse_value(o) for o in obj]

        elif isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, PRIMITIVES):
                    continue
                else:
                    obj[k] = self.traverse_value(v)
            return obj

        elif isinstance(obj, Base):
            self.detach_lineage.append(detach)
            _, base_obj = self.traverse_base(obj)
            return base_obj

        else:
            try:
                return obj.dict()
            except:
                SerializationException(
                    message=f"Failed to handle {type(obj)} in `BaseObjectSerializer.traverse_value`",
                    object=obj,
                )
                return str(obj)

    def detach_helper(self, ref_hash: str, obj: Any) -> Dict:
        if ref_hash in self.family_tree[self.leaf] and self.family_tree[self.leaf][
            ref_hash
        ] < len(self.detach_lineage):
            pass
        else:
            self.family_tree[self.leaf][ref_hash] = len(self.detach_lineage)

        self.traversed_objects[ref_hash] = obj

        return {
            "reference_id": ref_hash,
            "speckle_type": "reference",
        }
