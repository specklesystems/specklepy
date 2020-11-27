import json
import hashlib

from typing import Any, Dict, List, Tuple
from speckle.objects.base import Base
from speckle.logging.exceptions import SerializationException
from speckle.transports.abstract_transport import AbstractTransport

PRIMITIVES = (int, float, str, bool)


def hash_obj(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj).encode()).hexdigest()[:32]


class BaseObjectSerializer:
    write_transports: List[AbstractTransport]
    detach_lineage: List[bool] = []  # tracks depth and whether or not to detach
    family_tree: List[Dict[str, int]] = [{}]
    leaf: int = 0
    traversed_objects: Dict[str, Dict] = {}
    closure_table: Dict[str, Dict[str, int]] = {}

    def __init__(self, write_transports: List[AbstractTransport] = []) -> None:
        self.write_transports = write_transports

    def write_json(self, base: Base):
        self.detach_lineage = [True]
        hash, obj = self.traverse_base(base)
        return hash, json.dumps(obj)

    def traverse_base(self, base: Base) -> Tuple[str, Dict]:
        """Decomposes the given base object and builds a serializable dictionary

        Arguments:
            base {Base} -- the base object to be decomposed and serialized

        Returns:
            (str, dict) -- a tuple containing the hash (id) of the base object and the constructed serializable dictionary
        """
        if not self.detach_lineage:
            self.detach_lineage = [True]
        object_builder = {"id": ""}
        children = []
        obj, props = base, base.get_member_names()

        while props:
            prop = props.pop(0)
            value = obj[prop]
            detach = False

            # skip nulls or props marked to be ignored with "__"
            if not value or prop.startswith("__"):
                continue

            if prop.startswith("@"):
                detach = True

            # 1. handle primitives (ints, floats, strings, and bools)
            if isinstance(value, PRIMITIVES):
                object_builder[prop] = value
                continue

            # 2. handle lists and dicts
            elif isinstance(value, (list, dict)):
                self.leaf += 1
                self.family_tree.append({})

                if detach:
                    child_obj = self.traverse_value(value, detach=True)
                    ref_hash = hash_obj(child_obj)

                else:
                    child_obj = self.traverse_value(value)

                self.leaf -= 1
                for hash, depth in self.family_tree.pop().items():
                    if (
                        hash in self.family_tree[self.leaf]
                        and self.family_tree[self.leaf][hash] < depth
                    ):
                        pass
                    else:
                        self.family_tree[self.leaf][hash] = depth

            # 3. handle all other cases (nested Base objects, other objects, etc)
            elif detach:
                # self.detach_lineage.append(True)
                child_obj = self.traverse_value(value, detach=True)
                if isinstance(value, Base):
                    ref_hash = child_obj["id"]
                else:
                    ref_hash = hash_obj(child_obj)

            else:
                # self.detach_lineage.append(False)
                child_obj = self.traverse_value(value)

            # save child object (or the referenced to the detached child) to the object builder
            if detach:
                children.append(ref_hash)
                object_builder[prop] = self.detach_helper(
                    ref_hash=ref_hash, obj=child_obj
                )
            else:
                object_builder[prop] = child_obj

        hash = hash_obj(object_builder)
        object_builder["id"] = hash

        lineage = self.detach_lineage.pop() if self.detach_lineage else False

        # add closures to object and to closure table
        if children:
            lineage_length = len(self.detach_lineage)
            object_builder["__closure"] = self.closure_table[hash] = {
                hash: minDepth - lineage_length if lineage_length > 0 else minDepth
                for hash, minDepth in self.family_tree[self.leaf].items()
            }

        # write detached or root objects to transports
        if lineage:
            self.traversed_objects[hash] = object_builder
            self.write_to_transports(hash, object_builder)

        return hash, object_builder

    def traverse_value(self, obj: Any, detach: bool = False) -> Any:
        """Decomposes a given object and constructs a serializable object or dictionary

        Arguments:
            obj {Any} -- the value to decompose

        Returns:
            Any -- a serializable version of the given object
        """
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

    def detach_helper(self, ref_hash: str, obj: Any) -> Dict[str, str]:
        """Helper to keep track of detached objects and their depth in the family tree, write fully traversed objects, and create reference objects to place in the parent object

        Arguments:
            ref_hash {str} -- the hash of the fully traversed object
            obj {Any} -- the fully traversed object

        Returns:
            dict -- a reference object to be inserted into the given object's parent
        """
        if ref_hash in self.family_tree[self.leaf] and self.family_tree[self.leaf][
            ref_hash
        ] < len(self.detach_lineage):
            pass
        else:
            self.family_tree[self.leaf][ref_hash] = len(self.detach_lineage)

        return {
            "reference_id": ref_hash,
            "speckle_type": "reference",
        }

    def write_to_transports(self, hash: str, obj: Dict) -> None:
        for t in self.write_transports:
            t.save_object(id=hash, serialized_object=json.dumps(obj))
