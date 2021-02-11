"""This is an example module for automated base model subtype registration."""
from pydantic import BaseModel
from typing import ClassVar, Dict, Type


class ExampleBase(BaseModel):
    foo: int

    _registry : ClassVar[Dict[str, Type["ExampleBase"]]] = {}

    def __init_subclass__(cls, speckle_type:str, **kwargs):
        # this requires some validation, there is nothing blocking identical keys...
        cls.speckle_type = speckle_type
        ExampleBase._registry[speckle_type] = cls
        super().__init_subclass__(**kwargs)


class ExampleSub(ExampleBase, speckle_type="sub"):
    bar: str


class SpeckleSub(ExampleSub, speckle_type="speckle_sub"):
    magic : str


# # uncommenting this raises an error, for missing speckle_type definition
# # this automatically enforces mandatory type definition for everyone
# class FaultySub(ExampleBase):
    # pass


if __name__ == "__main__":

    for k,v in ExampleBase._registry.items():
        print(f"Speckle type {k}, mapped to {v.__name__}")

    print(ExampleBase._registry["speckle_sub"](foo=123, magic="trick", bar="baric").json())    