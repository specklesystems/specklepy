from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Any, Collection, Generator, Iterable, Iterator, List, Optional, Set, final
from specklepy.objects import Base


class AbstractTraversalRule(ABC):

    @abstractmethod
    def get_members_to_traverse(self, o: Base) -> Set[str]:
        return []

    @abstractmethod
    def does_rule_hold(self, o: Base) -> bool:
        return True

@final
class DefaultRule(AbstractTraversalRule):

    def get_members_to_traverse(self, _) -> Set[str]:
        return set()

    def does_rule_hold(self, _) -> bool:
        return True

@final
@dataclass(frozen=True, slots=True)
class TraversalContext:
    current: Base
    member_name: Optional[str] = None
    parent: Optional["TraversalContext"] = None

@final
@dataclass(frozen=True, slots=True)
class GraphTraversal:

    _rules: List[AbstractTraversalRule]

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
                self.traverse_member_to_stack(stack, current[child_prop], child_prop, head)
            
    @staticmethod
    def traverse_member_to_stack(stack: List[TraversalContext], value: Any, member_name: Optional[str] = None, parent: Optional[TraversalContext] = None):
        if isinstance(value, Base):
            stack.append(TraversalContext(value, member_name, parent))
        elif isinstance(value, list):
            for obj in value:
                GraphTraversal.traverse_member_to_stack(stack, obj, member_name, parent)
        elif isinstance(value, dict):
            for obj in value.values():
                GraphTraversal.traverse_member_to_stack(stack, obj, member_name, parent)

    def _get_active_rule_or_default_rule(self, o: Base) -> AbstractTraversalRule:
        return self._get_active_rule(o) or DefaultRule()

    def _get_active_rule(self, o: Base) -> Optional[AbstractTraversalRule]:
        for rule in self._rules:
            if rule.does_rule_hold(o):
                return rule
        return None

@final
@dataclass(slots=True)
class TraversalRule(AbstractTraversalRule):
    _conditions: Collection[Callable[[Base], bool]]
    _members_to_traverse: Callable[[Base], Iterable[str]]

    def get_members_to_traverse(self, o: Base) -> Set[str]:
        return set(self._members_to_traverse(o))

    def does_rule_hold(self, o: Base) -> bool:
        for condition in self._conditions:
            if(condition(o)):
                return True
        return False
