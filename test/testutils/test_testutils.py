from rdflib.graph import Graph
from . import GraphHelper
import pytest


@pytest.mark.parametrize(
    "equal, format, lhs_data, rhs_data, ignore_blanks",
    [
        (
            False,
            "turtle",
            """
            @prefix eg: <ex:> .
            _:a _:b _:c .
            eg:o0 eg:p0 eg:s0 .
            eg:o1 eg:p1 eg:s1 .
            """,
            """
            @prefix eg: <ex:> .
            eg:o0 eg:p0 eg:s0 .
            eg:o1 eg:p1 eg:s1 .
            """,
            False,
        ),
        (
            True,
            "turtle",
            """
            @prefix eg: <ex:> .
            _:a _:b _:c .
            eg:o0 eg:p0 eg:s0 .
            eg:o1 eg:p1 eg:s1 .
            """,
            """
            @prefix eg: <ex:> .
            eg:o0 eg:p0 eg:s0 .
            eg:o1 eg:p1 eg:s1 .
            """,
            True,
        ),
        (
            True,
            "turtle",
            """
            <ex:o0> <ex:p0> <ex:s0> .
            <ex:o1> <ex:p1> <ex:s1> .
            """,
            """
            @prefix eg: <ex:> .
            eg:o0 eg:p0 eg:s0 .
            eg:o1 eg:p1 eg:s1 .
            """,
            False,
        ),
        (
            False,
            "turtle",
            """
            <ex:o0> <ex:p0> <ex:s0> .
            <ex:o1> <ex:p1> <ex:s1> .
            <ex:o2> <ex:p2> <ex:s2> .
            """,
            """
            @prefix eg: <ex:> .
            eg:o0 eg:p0 eg:s0 .
            eg:o1 eg:p1 eg:s1 .
            """,
            False,
        ),
    ],
)
def test_assert_triples_equal(
    equal: bool, format: str, lhs_data: str, rhs_data: str, ignore_blanks: bool
):
    lhs_graph = Graph().parse(data=lhs_data, format=format)
    rhs_graph = Graph().parse(data=rhs_data, format=format)
    GraphHelper.assert_triples_equal(lhs_graph, lhs_graph, True)
    GraphHelper.assert_triples_equal(rhs_graph, rhs_graph, True)
    if not equal:
        with pytest.raises(AssertionError):
            GraphHelper.assert_triples_equal(lhs_graph, rhs_graph, ignore_blanks)
    else:
        GraphHelper.assert_triples_equal(lhs_graph, rhs_graph, ignore_blanks)
