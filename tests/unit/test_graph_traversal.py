from dataclasses import dataclass
from typing import Dict, List, Optional
from unittest import TestCase

from specklepy.objects.base import Base
from specklepy.objects.graph_traversal.traversal import GraphTraversal, TraversalRule


@dataclass()
class TraversalMock(Base):
    child: Optional[Base]
    list_children: List[Base]
    dict_children: Dict[str, Base]


class GraphTraversalTests(TestCase):
    def test_traverse_list_members(self):
        traverse_lists_rule = TraversalRule(
            [lambda _: True],
            lambda x: [
                item
                for item in x.get_member_names()
                if isinstance(getattr(x, item, None), list)
            ],
        )

        expected_traverse = Base()
        expected_traverse.id = "List Member"

        expected_ignore = Base()
        expected_ignore.id = "Not List Member"

        test_case = TraversalMock(
            list_children=[expected_traverse],
            dict_children={"myprop": expected_ignore},
            child=expected_ignore,
        )

        ret = [
            context.current
            for context in GraphTraversal([traverse_lists_rule]).traverse(test_case)
        ]

        self.assertCountEqual(ret, [test_case, expected_traverse])
        self.assertNotIn(expected_ignore, ret)
        self.assertEqual(len(ret), 2)

    def test_traverse_dict_members(self):
        traverse_lists_rule = TraversalRule(
            [lambda _: True],
            lambda x: [
                item
                for item in x.get_member_names()
                if isinstance(getattr(x, item, None), dict)
            ],
        )

        expected_traverse = Base()
        expected_traverse.id = "Dict Member"

        expected_ignore = Base()
        expected_ignore.id = "Not Dict Member"

        test_case = TraversalMock(
            list_children=[expected_ignore],
            dict_children={"myprop": expected_traverse},
            child=expected_ignore,
        )

        ret = [
            context.current
            for context in GraphTraversal([traverse_lists_rule]).traverse(test_case)
        ]

        self.assertCountEqual(ret, [test_case, expected_traverse])
        self.assertNotIn(expected_ignore, ret)
        self.assertEqual(len(ret), 2)

    def test_traverse_dynamic(self):
        traverse_lists_rule = TraversalRule(
            [lambda _: True], lambda x: x.get_dynamic_member_names()
        )

        expected_traverse = Base()
        expected_traverse.id = "List Member"

        expected_ignore = Base()
        expected_ignore.id = "Not List Member"

        test_case = TraversalMock(
            child=expected_ignore,
            list_children=[expected_ignore],
            dict_children={"myprop": expected_ignore},
        )
        test_case["dynamicChild"] = expected_traverse
        test_case["dynamicListChild"] = [expected_traverse]

        ret = [
            context.current
            for context in GraphTraversal([traverse_lists_rule]).traverse(test_case)
        ]

        self.assertCountEqual(ret, [test_case, expected_traverse, expected_traverse])
        self.assertNotIn(expected_ignore, ret)
        self.assertEqual(len(ret), 3)
