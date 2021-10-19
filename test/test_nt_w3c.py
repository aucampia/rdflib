"""This runs the nt tests for the W3C RDF Working Group's N-Quads
test suite."""
import os

from rdflib import Graph
from test import TEST_DIR
from test.manifest import RDFT, read_manifest

from test.testutils import nose_tst_earl_report
import pytest

verbose = False


def nt(test):
    g = Graph()

    try:
        g.parse(test.action, format="nt")
        if not test.syntax:
            raise AssertionError("Input shouldn't have parsed!")
    except:
        if test.syntax:
            raise


testers = {RDFT.TestNTriplesPositiveSyntax: nt, RDFT.TestNTriplesNegativeSyntax: nt}


@pytest.mark.parametrize(
    "type,test",
    read_manifest(os.path.join(TEST_DIR, "w3c/nt/manifest.ttl"), legacy=True),
)
def test_manifest(type, test):
    testers[type](test)


if __name__ == "__main__":
    # TODO FIXME: generate report.
    pass
