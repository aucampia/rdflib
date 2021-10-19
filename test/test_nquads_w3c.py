"""This runs the nquads tests for the W3C RDF Working Group's N-Quads
test suite."""

from rdflib import ConjunctiveGraph
from test.manifest import RDFT, read_manifest
import pytest

verbose = False


def nquads(test):
    g = ConjunctiveGraph()

    try:
        g.parse(test.action, format="nquads")
        if not test.syntax:
            raise AssertionError("Input shouldn't have parsed!")
    except:
        if test.syntax:
            raise


testers = {RDFT.TestNQuadsPositiveSyntax: nquads, RDFT.TestNQuadsNegativeSyntax: nquads}


@pytest.mark.parametrize(
    "type,test",
    read_manifest("test/w3c/nquads/manifest.ttl"),
)
def test_manifest(type, test):
    testers[type](test)


if __name__ == "__main__":
    # TODO FIXME: generate report.
    pass
