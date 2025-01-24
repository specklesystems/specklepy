from specklepy.objects.base import Base
from specklepy.objects.graph_traversal.traversal import GraphTraversal, TraversalRule

DISPLAY_VALUE_PROPERTY_ALIASES = {"displayValue", "@displayValue"}
ELEMENTS_PROPERTY_ALIASES = {"elements", "@elements"}


def has_display_value(x: Base):
    return any(hasattr(x, alias) for alias in DISPLAY_VALUE_PROPERTY_ALIASES)


def create_default_traversal_function() -> GraphTraversal:
    """
    Traversal func for traversing the root object of a Speckle Model
    """

    convertible_rule = TraversalRule(
        [lambda b: b.speckle_type != "Base", has_display_value],
        lambda _: ELEMENTS_PROPERTY_ALIASES,
    )

    default_rule = TraversalRule(
        [lambda _: True],
        # NOTE: Unlike the C# implementation, this does not ignore Obsolete members
        lambda o: o.get_member_names(),
        False,
    )

    return GraphTraversal([convertible_rule, default_rule])
