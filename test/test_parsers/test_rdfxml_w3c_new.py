from test.manifest import RDFT, RDFTest, read_manifest

import pytest


@pytest.mark.parametrize(
    "rdf_test_uri, type, rdf_test",
    read_manifest(
        os.path.join(TEST_DATA_DIR, "suites", "w3c/ntriples/manifest.ttl"), legacy=True
    ),
)
def test_manifest(rdf_test_uri: URIRef, type: Node, rdf_test: RDFTest):
    testers[type](rdf_test)
