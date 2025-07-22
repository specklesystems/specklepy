from typing import cast

from ifcopenshell.entity_instance import entity_instance
from specklepy.objects.base import Base
from specklepy.objects.models.collections.collection import Collection


def project_to_speckle(
    step_element: entity_instance, children: list[Base]
) -> Collection:
    guid = cast(str, step_element.GlobalId)
    name = cast(str, step_element.Name or step_element.LongName or guid)

    project = Collection(applicationId=guid, name=name, elements=children)

    project["ifcType"] = step_element.is_a()
    project["description"] = step_element.Description
    project["objectType"] = step_element.ObjectType
    project["longName"] = step_element.LongName
    project["phase"] = step_element.Phase

    return project
