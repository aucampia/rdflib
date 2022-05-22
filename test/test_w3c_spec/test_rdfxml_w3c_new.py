import logging
from contextlib import ExitStack
from pathlib import Path
from test.data import TEST_DATA_DIR
from test.utils import BNodeHandling, GraphHelper
from test.utils.iri import file_uri_to_path, rebase_url
from test.utils.namespace import RDFT
from test.utils.rdftest import ManifestEntry, local_file_path, params_from_sources
from typing import Callable, Dict, Optional

import pytest

from rdflib.exceptions import ParserError
from rdflib.graph import Graph
from rdflib.namespace import RDF
from rdflib.term import URIRef

# def test_equals() -> None:
#     assert URIRef("http://www.w3.org/ns/rdftest#TestXMLEval") == RDFT.TestXMLEval

REMOTE_BASE_IRI = "http://www.w3.org/2013/RDFXMLTests/"
LOCAL_BASE_DIR = TEST_DATA_DIR / "suites/w3c/rdf-xml/"

logger = logging.getLogger(__name__)

VALID_TYPES = {RDFT.TestXMLNegativeSyntax, RDFT.TestXMLEval}


def check_entry(entry: ManifestEntry) -> None:
    assert entry.mf_action is not None
    assert entry.type in VALID_TYPES
    action_local = rebase_url(entry.mf_action, REMOTE_BASE_IRI, LOCAL_BASE_DIR.as_uri())
    action_local = rebase_url(entry.mf_action, REMOTE_BASE_IRI, LOCAL_BASE_DIR.as_uri())
    if logger.isEnabledFor(logging.DEBUG):
        action_path = file_uri_to_path(action_local, Path)
        logger.debug("action = %s\n%s", action_path, action_path.read_text())
    catcher: Optional[pytest.ExceptionInfo[Exception]] = None
    with ExitStack() as xstack:
        if entry.type == RDFT.TestXMLNegativeSyntax:
            catcher = xstack.enter_context(pytest.raises(Exception))
        graph = Graph()
        graph.parse(action_local, publicID=entry.mf_action, format="xml")
        if entry.type == RDFT.TestXMLEval:
            assert entry.mf_result is not None
            result_source = rebase_url(
                entry.mf_result, REMOTE_BASE_IRI, LOCAL_BASE_DIR.as_uri()
            )
            result_graph = Graph()
            result_graph.parse(
                result_source, publicID=entry.mf_action, format="ntriples"
            )
            GraphHelper.assert_isomorphic(graph, result_graph)
            GraphHelper.assert_sets_equals(
                graph,
                result_graph,
                bnode_handling=BNodeHandling.COLLAPSE,
            )
    if catcher is not None:
        assert catcher.value is not None


@pytest.mark.parametrize(
    ["manifest_entry"],
    params_from_sources(
        LOCAL_BASE_DIR / "manifest.ttl",
        public_id=REMOTE_BASE_IRI,
    ),
)
def test_entry(manifest_entry: ManifestEntry) -> None:
    check_entry(manifest_entry)
