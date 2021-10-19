"""This runs the turtle tests for the W3C RDF Working Group's N-Quads
test suite."""

from rdflib import Graph
from rdflib.namespace import split_uri
from rdflib.compare import graph_diff, isomorphic

from test.manifest import RDFT, read_manifest
import pytest

verbose = False


def turtle(test):
    g = Graph()

    try:
        base = "http://www.w3.org/2013/TurtleTests/" + split_uri(test.action)[1]

        g.parse(test.action, publicID=base, format="turtle")
        if not test.syntax:
            raise AssertionError("Input shouldn't have parsed!")

        if test.result:  # eval test
            res = Graph()
            res.parse(test.result, format="nt")

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

            assert isomorphic(g, res), "graphs must be the same"

    except:
        if test.syntax:
            raise


testers = {
    RDFT.TestTurtlePositiveSyntax: turtle,
    RDFT.TestTurtleNegativeSyntax: turtle,
    RDFT.TestTurtleEval: turtle,
    RDFT.TestTurtleNegativeEval: turtle,
}


@pytest.mark.parametrize(
    "type,test",
    read_manifest("test/w3c/turtle/manifest.ttl"),
)
def test_manifest(type, test):
    testers[type](test)


if __name__ == "__main__":
    # TODO FIXME: generate report.
    pass
