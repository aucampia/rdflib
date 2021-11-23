"""This runs the turtle tests for the W3C RDF Working Group's N-Quads
test suite."""

from pathlib import Path
from typing import Callable, Dict
from rdflib import Graph
from rdflib.namespace import split_uri
from rdflib.compare import graph_diff, isomorphic
from rdflib.term import Node, URIRef

from test.manifest import RDFT, RDFTest, read_manifest
import pytest
from .testutils import file_uri_to_path

verbose = False


def turtle(test: RDFTest):
    g = Graph()

    try:
        base = "http://www.w3.org/2013/TurtleTests/" + split_uri(test.action)[1]

        action_path = file_uri_to_path(test.action, Path)

        with action_path.open("rb") as fh:
            g.parse(fh, publicID=base, format="turtle")
        # g.parse(test.action, publicID=base, format="turtle")
        if not test.syntax:
            raise AssertionError("Input shouldn't have parsed!")

        if test.result:  # eval test
            result_path = file_uri_to_path(test.result, Path)
            res = Graph()
            with result_path.open("r", newline="\n") as fh:
                res.parse(fh, format="nt")

            if verbose:
                both, first, second = graph_diff(g, res)
                if not first and not second:
                    return
                print("Diff:")
                # print "%d triples in both"%len(both)
                print("Turtle Only:")
                for t in first:
                    print(t)

                print("--------------------")
                print("NT Only")
                for t in second:
                    print(t)
                raise Exception("Graphs do not match!")

            assert isomorphic(g, res), "graphs must be the same, expected\n%s\n, got\n%s" % ( g.serialize(), res.serialize() )

    except:
        if test.syntax:
            raise


testers: Dict[Node, Callable[[RDFTest], None]] = {
    RDFT.TestTurtlePositiveSyntax: turtle,
    RDFT.TestTurtleNegativeSyntax: turtle,
    RDFT.TestTurtleEval: turtle,
    RDFT.TestTurtleNegativeEval: turtle,
}


@pytest.mark.parametrize(
    "rdf_test_uri, type, rdf_test",
    read_manifest("test/w3c/turtle/manifest.ttl"),
)
def test_manifest(rdf_test_uri: URIRef, type: Node, rdf_test: RDFTest):
    testers[type](rdf_test)
