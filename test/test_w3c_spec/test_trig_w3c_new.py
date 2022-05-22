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
from rdflib.graph import Dataset, Graph
from rdflib.namespace import RDF
from rdflib.term import URIRef

# def test_equals() -> None:
#     assert URIRef("http://www.w3.org/ns/rdftest#TestXMLEval") == RDFT.TestXMLEval

REMOTE_BASE_IRI = "http://www.w3.org/2013/TriGTests/"
LOCAL_BASE_DIR = TEST_DATA_DIR / "suites/w3c/trig/"

logger = logging.getLogger(__name__)

VALID_TYPES = {
    RDFT.TestTrigEval,
    RDFT.TestTrigPositiveSyntax,
    RDFT.TestTrigNegativeSyntax,
    RDFT.TestTrigNegativeEval,
}


def check_entry(entry: ManifestEntry) -> None:
    assert entry.mf_action is not None
    assert entry.type in VALID_TYPES
    action_local = rebase_url(entry.mf_action, REMOTE_BASE_IRI, LOCAL_BASE_DIR.as_uri())
    catcher: Optional[pytest.ExceptionInfo[Exception]] = None
    if logger.isEnabledFor(logging.DEBUG):
        action_path = file_uri_to_path(action_local, Path)
        logger.debug("action = %s\n%s", action_path, action_path.read_text())
    with ExitStack() as xstack:
        if entry.type in (RDFT.TestTrigNegativeSyntax, RDFT.TestTrigNegativeEval):
            catcher = xstack.enter_context(pytest.raises(Exception))
        dataset = Dataset()
        dataset.parse(action_local, publicID=entry.mf_action, format="trig")
        if entry.type == RDFT.TestTrigEval:
            assert entry.mf_result is not None
            result_source = rebase_url(
                entry.mf_result, REMOTE_BASE_IRI, LOCAL_BASE_DIR.as_uri()
            )
            result_dataset = Dataset()
            result_dataset.parse(
                result_source, publicID=entry.mf_action, format="nquads"
            )
            GraphHelper.assert_sets_equals(
                dataset, result_dataset, bnode_handling=BNodeHandling.COLLAPSE
            )
    if catcher is not None:
        assert catcher.value is not None


@pytest.mark.parametrize(
    ["manifest_entry"],
    params_from_sources(
        LOCAL_BASE_DIR / "manifest.ttl",
        public_id=REMOTE_BASE_IRI,
        mark_dict={
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-base-04": pytest.mark.xfail(
                reason="accepts @base in the wrong place"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-base-05": pytest.mark.xfail(
                reason="accepts BASE in the wrong place"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-prefix-06": pytest.mark.xfail(
                reason="accepts @prefix in the wrong place"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-prefix-07": pytest.mark.xfail(
                reason="accepts PREFIX in the wrong place"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-LITERAL2_with_langtag_and_datatype": pytest.mark.xfail(
                reason="accepts literal with langtag and datatype"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-uri-01": pytest.mark.xfail(
                reason="accepts an invalid IRI"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-uri-02": pytest.mark.xfail(
                reason="accepts an invalid IRI"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-uri-03": pytest.mark.xfail(
                reason="accepts an invalid IRI"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-uri-04": pytest.mark.xfail(
                reason="accepts an invalid IRI"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-uri-05": pytest.mark.xfail(
                reason="accepts an invalid IRI"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-struct-04": pytest.mark.xfail(
                reason="allows literal as subject"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-struct-05": pytest.mark.xfail(
                reason="allows literal as predicate"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-struct-06": pytest.mark.xfail(
                reason="allows BNodes as predicate"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-struct-07": pytest.mark.xfail(
                reason="allows BNodes as predicate"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-kw-04": pytest.mark.xfail(
                reason="accepts 'true' as a subject"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-kw-05": pytest.mark.xfail(
                reason="accepts 'true' as a predicate"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-n3-extras-03": pytest.mark.xfail(
                reason="accepts N3 paths"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-n3-extras-04": pytest.mark.xfail(
                reason="accepts N3 paths"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-n3-extras-06": pytest.mark.xfail(
                reason="accepts N3 paths"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-struct-12": pytest.mark.xfail(
                reason="ingores bad triples"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-struct-14": pytest.mark.xfail(
                reason="accepts literal as subject"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-struct-15": pytest.mark.xfail(
                reason="accepts literal as predicate"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-struct-16": pytest.mark.xfail(
                reason="accepts BNode as predicate"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-struct-17": pytest.mark.xfail(
                reason="accepts BNode as predicate"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-esc-02": pytest.mark.xfail(
                reason="accepts badly escaped literals"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-esc-03": pytest.mark.xfail(
                reason="accepts badly escaped literals"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-esc-04": pytest.mark.xfail(
                reason="accepts badly escaped literals"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-string-06": pytest.mark.xfail(
                reason="accepts badly quoted literals"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-string-07": pytest.mark.xfail(
                reason="accepts badly quoted literals"
            ),
            f"{REMOTE_BASE_IRI}#trig-eval-bad-01": pytest.mark.xfail(
                reason="accepts bad IRI"
            ),
            f"{REMOTE_BASE_IRI}#trig-eval-bad-02": pytest.mark.xfail(
                reason="accepts bad IRI"
            ),
            f"{REMOTE_BASE_IRI}#trig-eval-bad-03": pytest.mark.xfail(
                reason="accepts bad IRI"
            ),
            f"{REMOTE_BASE_IRI}#trig-eval-bad-04": pytest.mark.xfail(
                reason="accepts bad IRI"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-ln-dash-start": pytest.mark.xfail(
                reason="accepts dash in start of local name"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-list-01": pytest.mark.xfail(
                reason="ignores badly formed quad"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-list-02": pytest.mark.xfail(
                reason="ignores badly formed quad"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-list-03": pytest.mark.xfail(
                reason="ignores badly formed quad"
            ),
            f"{REMOTE_BASE_IRI}#trig-syntax-bad-list-04": pytest.mark.xfail(
                reason="ignores badly formed quad"
            ),
            f"{REMOTE_BASE_IRI}#trig-graph-bad-01": pytest.mark.xfail(
                reason="accepts GRAPH with no name"
            ),
            f"{REMOTE_BASE_IRI}#trig-graph-bad-07": pytest.mark.xfail(
                reason="accepts nested GRAPH"
            ),
        },
    ),
)
def test_entry(manifest_entry: ManifestEntry) -> None:
    check_entry(manifest_entry)
