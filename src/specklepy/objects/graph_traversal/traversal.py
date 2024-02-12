from typing import Any, Callable, Collection, Iterable, Iterator, List, Optional, Set

from attrs import define
from typing_extensions import Protocol, final

from specklepy.objects.base import Base


class ITraversalRule(Protocol):
    def get_members_to_traverse(self, o: Base) -> Set[str]:
        """Get the members to traverse."""
        pass

    def does_rule_hold(self, o: Base) -> bool:
        """Make sure the rule still holds."""
        pass


@final
@define(slots=True, frozen=True)
class DefaultRule:
    def get_members_to_traverse(self, _) -> Set[str]:
        return set()

    def does_rule_hold(self, _) -> bool:
        return True


# we're creating a local protected "singleton"
_default_rule = DefaultRule()


@final
@define(slots=True, frozen=True)
class TraversalContext:
    current: Base
    member_name: Optional[str] = None
    parent: Optional["TraversalContext"] = None


@final
@define(slots=True, frozen=True)
class GraphTraversal:
    _rules: List[ITraversalRule]

    def traverse(self, root: Base) -> Iterator[TraversalContext]:
        stack: List[TraversalContext] = []

        stack.append(TraversalContext(root))

        while len(stack) > 0:
            head = stack.pop()
            yield head

            current = head.current
            active_rule = self._get_active_rule_or_default_rule(current)
            members_to_traverse = active_rule.get_members_to_traverse(current)
            for child_prop in members_to_traverse:
                try:
                    if child_prop in {"speckle_type", "units", "applicationId"}:
                        continue  # debug: to avoid noisy exceptions, explicitly avoid checking ones we know will fail, this is not exhaustive
                    if getattr(current, child_prop, None):
                        value = current[child_prop]
                        self._traverse_member_to_stack(stack, value, child_prop, head)
                except KeyError:
                    # Unset application ids, and class variables like SpeckleType will throw when __getitem__ is called
                    pass

    @staticmethod
    def _traverse_member_to_stack(
        stack: List[TraversalContext],
        value: Any,
        member_name: Optional[str] = None,
        parent: Optional[TraversalContext] = None,
    ):
        if isinstance(value, Base):
            stack.append(TraversalContext(value, member_name, parent))
        elif isinstance(value, list):
            for obj in value:
                GraphTraversal._traverse_member_to_stack(
                    stack, obj, member_name, parent
                )
        elif isinstance(value, dict):
            for obj in value.values():
                GraphTraversal._traverse_member_to_stack(
                    stack, obj, member_name, parent
                )

    @staticmethod
    def traverse_member(value: Optional[Any]) -> Iterator[Base]:
        if isinstance(value, Base):
            yield value
        elif isinstance(value, list):
            for obj in value:
                for o in GraphTraversal.traverse_member(obj):
                    yield o
        elif isinstance(value, dict):
            for obj in value.values():
                for o in GraphTraversal.traverse_member(obj):
                    yield o

    def _get_active_rule_or_default_rule(self, o: Base) -> ITraversalRule:
        return self._get_active_rule(o) or _default_rule

    def _get_active_rule(self, o: Base) -> Optional[ITraversalRule]:
        for rule in self._rules:
            if rule.does_rule_hold(o):
                return rule
        return None


@final
@define(slots=True, frozen=True)
class TraversalRule:
    _conditions: Collection[Callable[[Base], bool]]
    _members_to_traverse: Callable[[Base], Iterable[str]]

    def get_members_to_traverse(self, o: Base) -> Set[str]:
        return set(self._members_to_traverse(o))

    def does_rule_hold(self, o: Base) -> bool:
        for condition in self._conditions:
            if condition(o):
                return True
        return False
